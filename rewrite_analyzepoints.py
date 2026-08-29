import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r"fun analyzePoints.*?return V4RunResult\(success = true, errorMessage = \"OK\", axis = axisDeg.*?$"

replacement = """fun analyzePoints(matchedRef: List<Point>, matchedLens: List<Point>, w: Double, h: Double, baseRefDotCount: Int = 0, baseLensDotCount: Int = 0, spacing: Double = 30.0, rejections: MutableMap<String, Int> = mutableMapOf()): V4RunResult {
        try {
            val cx = w / 2.0
            val cy = h / 2.0
            val rMax = min(w, h) / 2.0
            
            val anchorRef = mutableListOf<Point>()
            val anchorLens = mutableListOf<Point>()
            val measurementRef = mutableListOf<Point>()
            val measurementLens = mutableListOf<Point>()
            
            val innerRadiusSq = (rMax * 0.7) * (rMax * 0.7)
            
            for (i in matchedRef.indices) {
                val pt = matchedRef[i]
                val dSq = (pt.x - cx) * (pt.x - cx) + (pt.y - cy) * (pt.y - cy)
                if (dSq > innerRadiusSq) {
                    anchorRef.add(matchedRef[i])
                    anchorLens.add(matchedLens[i])
                } else {
                    measurementRef.add(matchedRef[i])
                    measurementLens.add(matchedLens[i])
                }
            }
            
            var globalScaleAmbiguous = false
            var registrationRms = 0.0
            var inliersCount = 0
            
            val useRigidFallback = anchorRef.size < 15
            if (useRigidFallback) {
                globalScaleAmbiguous = true
            }
            
            val srcMat = MatOfPoint2f()
            val dstMat = MatOfPoint2f()
            
            if (useRigidFallback) {
                srcMat.fromList(matchedLens)
                dstMat.fromList(matchedRef)
            } else {
                srcMat.fromList(anchorLens)
                dstMat.fromList(anchorRef)
            }
            
            val mask = Mat()
            val transformMat: Mat
            
            val ransacThresh = if (useRigidFallback) max(15.0, spacing * 0.8) else max(5.0, spacing * 0.4)
            
            if (useRigidFallback) {
                if (matchedRef.size < 3) {
                     return V4RunResult(success = false, errorMessage = "Insufficient matched points (<3)", candidateMatches = matchedRef.size, matchRejections = rejections)
                }
                transformMat = Calib3d.estimateAffinePartial2D(srcMat, dstMat, mask, Calib3d.RANSAC, ransacThresh)
            } else {
                if (anchorRef.size < 4) {
                     return V4RunResult(success = false, errorMessage = "Insufficient anchors (<4)", candidateMatches = matchedRef.size, matchRejections = rejections)
                }
                transformMat = Calib3d.findHomography(srcMat, dstMat, Calib3d.RANSAC, ransacThresh, mask)
            }
            
            if (transformMat.empty()) {
                rejections["registration_inconsistency"] = rejections.getOrDefault("registration_inconsistency", 0) + matchedRef.size
                return V4RunResult(success = false, errorMessage = "Registration failed", candidateMatches = matchedRef.size, matchRejections = rejections)
            }
            
            val maskArray = ByteArray(mask.rows() * mask.cols())
            mask.get(0, 0, maskArray)
            inliersCount = maskArray.count { it.toInt() != 0 }
            
            // Optical points to measure: Always all topology matches
            val ptsToMeasureRef = matchedRef.toMutableList()
            val ptsToMeasureLens = matchedLens.toMutableList()
            
            val srcMeasMat = MatOfPoint2f()
            srcMeasMat.fromList(ptsToMeasureLens)
            val dstMeasMat = MatOfPoint2f()
            
            if (useRigidFallback) {
                Core.transform(srcMeasMat, dstMeasMat, transformMat)
            } else {
                Core.perspectiveTransform(srcMeasMat, dstMeasMat, transformMat)
            }
            
            val transformedLens = dstMeasMat.toList()
            
            if (!useRigidFallback) {
                var rSum = 0.0
                val anchorLensTransformed = MatOfPoint2f()
                Core.perspectiveTransform(srcMat, anchorLensTransformed, transformMat)
                val transformedAnchors = anchorLensTransformed.toList()
                for (i in anchorRef.indices) {
                    if (maskArray[i].toInt() != 0) {
                        val dx = transformedAnchors[i].x - anchorRef[i].x
                        val dy = transformedAnchors[i].y - anchorRef[i].y
                        rSum += dx * dx + dy * dy
                    }
                }
                registrationRms = sqrt(rSum / max(1, inliersCount))
            } else {
                var rSum = 0.0
                for (i in matchedRef.indices) {
                    if (maskArray[i].toInt() != 0) {
                        val dx = transformedLens[i].x - matchedRef[i].x
                        val dy = transformedLens[i].y - matchedRef[i].y
                        rSum += dx * dx + dy * dy
                    }
                }
                registrationRms = sqrt(rSum / max(1, inliersCount))
            }
            
            // IRLS for robust optical field fit
            val numMeas = ptsToMeasureRef.size
            if (numMeas < 6) {
                 return V4RunResult(success = false, errorMessage = "Insufficient measurement points (<6)", candidateMatches = matchedRef.size, acceptedMatches = inliersCount, matchRejections = rejections)
            }
            
            val A = Mat(numMeas, 3, CvType.CV_64F)
            val B = Mat(numMeas, 2, CvType.CV_64F)
            
            for (i in 0 until numMeas) {
                A.put(i, 0, ptsToMeasureRef[i].x)
                A.put(i, 1, ptsToMeasureRef[i].y)
                A.put(i, 2, 1.0)
                
                B.put(i, 0, transformedLens[i].x - ptsToMeasureRef[i].x)
                B.put(i, 1, transformedLens[i].y - ptsToMeasureRef[i].y)
            }
            
            val J_matrix = Mat(3, 2, CvType.CV_64F)
            var weights = DoubleArray(numMeas) { 1.0 }
            val huberK = 1.345
            
            var j00 = 0.0; var j10 = 0.0; var j01 = 0.0; var j11 = 0.0
            var c0 = 0.0; var c1 = 0.0
            
            for (iter in 0 until 5) {
                val AW = Mat(numMeas, 3, CvType.CV_64F)
                val BW = Mat(numMeas, 2, CvType.CV_64F)
                for (i in 0 until numMeas) {
                    val w = sqrt(weights[i])
                    AW.put(i, 0, A.get(i, 0)[0] * w)
                    AW.put(i, 1, A.get(i, 1)[0] * w)
                    AW.put(i, 2, A.get(i, 2)[0] * w)
                    
                    BW.put(i, 0, B.get(i, 0)[0] * w)
                    BW.put(i, 1, B.get(i, 1)[0] * w)
                }
                
                try {
                    Core.solve(AW, BW, J_matrix, Core.DECOMP_SVD)
                } catch (e: Exception) {
                    return V4RunResult(success = false, errorMessage = "IRLS solve failed: ${e.message}", candidateMatches = matchedRef.size, matchRejections = rejections)
                }
                
                j00 = J_matrix.get(0, 0)[0]
                j10 = J_matrix.get(0, 1)[0]
                j01 = J_matrix.get(1, 0)[0]
                j11 = J_matrix.get(1, 1)[0]
                c0 = J_matrix.get(2, 0)[0]
                c1 = J_matrix.get(2, 1)[0]
                
                val errors = DoubleArray(numMeas)
                for (i in 0 until numMeas) {
                    val x = A.get(i, 0)[0]
                    val y = A.get(i, 1)[0]
                    val errX = (j00 * x + j01 * y + c0) - B.get(i, 0)[0]
                    val errY = (j10 * x + j11 * y + c1) - B.get(i, 1)[0]
                    errors[i] = sqrt(errX * errX + errY * errY)
                }
                
                val sortedErrors = errors.sorted()
                val medianErr = sortedErrors[sortedErrors.size / 2]
                val sigma = max(medianErr / 0.6745, 1e-5)
                
                for (i in 0 until numMeas) {
                    val r = errors[i] / sigma
                    weights[i] = if (r <= huberK) 1.0 else huberK / r
                }
            }
            
            var opticalFieldRetainedCount = 0
            val finalPtsToMeasureRef = mutableListOf<Point>()
            var q1 = false; var q2 = false; var q3 = false; var q4 = false
            var minX = Double.MAX_VALUE; var maxX = -Double.MAX_VALUE
            var minY = Double.MAX_VALUE; var maxY = -Double.MAX_VALUE
            
            var fieldFitRmsSum = 0.0
            
            for (i in 0 until numMeas) {
                if (weights[i] > 0.5) {
                    opticalFieldRetainedCount++
                    val pt = ptsToMeasureRef[i]
                    finalPtsToMeasureRef.add(pt)
                    
                    if (pt.x < cx && pt.y < cy) q1 = true
                    if (pt.x >= cx && pt.y < cy) q2 = true
                    if (pt.x < cx && pt.y >= cy) q3 = true
                    if (pt.x >= cx && pt.y >= cy) q4 = true
                    
                    if (pt.x < minX) minX = pt.x
                    if (pt.x > maxX) maxX = pt.x
                    if (pt.y < minY) minY = pt.y
                    if (pt.y > maxY) maxY = pt.y
                    
                    val x = pt.x
                    val y = pt.y
                    val u = j00 * x + j01 * y + c0
                    val v = j10 * x + j11 * y + c1
                    
                    val dx = transformedLens[i].x - x
                    val dy = transformedLens[i].y - y
                    
                    fieldFitRmsSum += (u - dx) * (u - dx) + (v - dy) * (v - dy)
                }
            }
            
            val fieldFitRms = sqrt(fieldFitRmsSum / max(1, opticalFieldRetainedCount))
            
            val quadCount = (if (q1) 1 else 0) + (if (q2) 1 else 0) + (if (q3) 1 else 0) + (if (q4) 1 else 0)
            val spreadX = if (maxX > minX) maxX - minX else 0.0
            val spreadY = if (maxY > minY) maxY - minY else 0.0
            val spatialCoveragePct = ((spreadX * spreadY) / (w * h)) * 100.0
            
            if (opticalFieldRetainedCount < 6) {
                 return V4RunResult(success = false, errorMessage = "Insufficient retained measurement points (<6)", candidateMatches = matchedRef.size, acceptedMatches = opticalFieldRetainedCount, matchRejections = rejections)
            }
            
            if (quadCount < 2 || spreadX < w * 0.1 || spreadY < h * 0.1) {
                rejections["roi_rejection"] = rejections.getOrDefault("roi_rejection", 0) + opticalFieldRetainedCount
                return V4RunResult(success = false, errorMessage = "Poor spatial coverage (quads: $quadCount, spread: ${spreadX.toInt()}x${spreadY.toInt()})", candidateMatches = matchedRef.size, acceptedMatches = opticalFieldRetainedCount, matchRejections = rejections, spatialCoveragePct = spatialCoveragePct, quadrantCoverage = quadCount)
            }
            
            // Recompute SVDecomp for degeneracy check using just retained points
            val AW_final = Mat(opticalFieldRetainedCount, 3, CvType.CV_64F)
            for (i in 0 until opticalFieldRetainedCount) {
                AW_final.put(i, 0, finalPtsToMeasureRef[i].x)
                AW_final.put(i, 1, finalPtsToMeasureRef[i].y)
                AW_final.put(i, 2, 1.0)
            }
            val W = Mat(); val U = Mat(); val Vt = Mat()
            Core.SVDecomp(AW_final, W, U, Vt)
            
            var rank = 0
            var maxSingular = 0.0
            var minSingular = Double.MAX_VALUE
            for (i in 0 until W.rows()) {
                val s = W.get(i, 0)[0]
                if (s > maxSingular) maxSingular = s
                if (s > 1e-6) {
                    rank++
                    if (s < minSingular) minSingular = s
                }
            }
            val cond = if (minSingular > 0.0) maxSingular / minSingular else Double.MAX_VALUE
            var degeneracyStatus = "OK"
            if (rank < 3) {
                degeneracyStatus = "RANK_DEFICIENT"
            } else if (cond > 1e4 || cond.isNaN()) {
                degeneracyStatus = "ILL_CONDITIONED"
            }
            
            if (degeneracyStatus != "OK") {
                 return V4RunResult(success = false, errorMessage = "Degenerate geometric configuration: $degeneracyStatus",
                     candidateMatches = matchedRef.size, acceptedMatches = opticalFieldRetainedCount, matrixRank = rank, conditionNumber = cond, degeneracyStatus = degeneracyStatus, matchRejections = rejections)
            }
            
            if (j00.isNaN() || j10.isNaN() || j01.isNaN() || j11.isNaN() ||
                j00.isInfinite() || j10.isInfinite() || j01.isInfinite() || j11.isInfinite()) {
                return V4RunResult(success = false, errorMessage = "NaN/Infinity in optical field solution",
                     candidateMatches = matchedRef.size, acceptedMatches = opticalFieldRetainedCount, matrixRank = rank, conditionNumber = cond, degeneracyStatus = "NAN_INF", matchRejections = rejections)
            }
            
            val t = j00 + j11
            val d = j00 * j11 - j01 * j10
            val disc = t * t - 4 * d
            
            var l1 = 0.0; var l2 = 0.0
            if (disc >= 0) {
                l1 = (t + sqrt(disc)) / 2.0
                l2 = (t - sqrt(disc)) / 2.0
            } else {
                l1 = t / 2.0
                l2 = t / 2.0
            }
            
            if (abs(l2) > abs(l1)) {
                val temp = l1; l1 = l2; l2 = temp
            }
            
            val iso = (l1 + l2) / 2.0
            val aniso = (l1 - l2) / 2.0
            
            var axisRad = 0.0
            if (abs(j10 + j01) > 1e-6) {
                axisRad = 0.5 * atan2(j10 + j01, j00 - j11)
            }
            var axisDeg = axisRad * 180.0 / PI
            if (axisDeg < 0) axisDeg += 180.0
            
            var sumDx = 0.0; var sumDy = 0.0
            for (i in 0 until numMeas) {
                sumDx += (transformedLens[i].x - ptsToMeasureRef[i].x)
                sumDy += (transformedLens[i].y - ptsToMeasureRef[i].y)
            }
            val meanDx = sumDx / numMeas
            val meanDy = sumDy / numMeas
            
            return V4RunResult(
                success = true,
                errorMessage = "OK",
                axis = axisDeg,
                lambda1 = l1,
                lambda2 = l2,
                isotropic = iso,
                anisotropic = aniso,
                trackedDots = numMeas,
                topologyMatchCount = matchedRef.size,
                registrationFeatureCount = if (useRigidFallback) matchedRef.size else anchorRef.size,
                registrationInliers = inliersCount,
                registrationRms = registrationRms,
                opticalFieldInputCount = numMeas,
                opticalFieldRetainedCount = opticalFieldRetainedCount,
                fieldFitRms = fieldFitRms,
                refDotCount = baseRefDotCount,
                lensDotCount = baseLensDotCount,
                meanDx = meanDx,
                meanDy = meanDy,
                referencePoints = ptsToMeasureRef,
                observedPoints = transformedLens,
                refWidth = w.toInt(),
                refHeight = h.toInt(),
                globalScaleAmbiguous = globalScaleAmbiguous,
                candidateMatches = matchedRef.size,
                acceptedMatches = opticalFieldRetainedCount,
                matchRejections = rejections,
                spatialCoveragePct = spatialCoveragePct,
                quadrantCoverage = quadCount,
                matrixRank = rank,
                conditionNumber = cond,
                degeneracyStatus = degeneracyStatus
            )
        } catch (e: Exception) {
            Log.e("V4OpticalAnalyzer", "AnalyzePoints failed", e)
            return V4RunResult(success = false, errorMessage = "Exception: ${e.message}")
        }
    }
"""

content = re.sub(r"fun analyzePoints.*?(?=\n    fun drawVectorMapInternal)", replacement, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
