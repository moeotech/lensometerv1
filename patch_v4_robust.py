import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

analyze_points_replacement = """    fun analyzePoints(matchedRef: List<Point>, matchedLens: List<Point>, w: Double, h: Double, baseRefDotCount: Int = 0, baseLensDotCount: Int = 0): V4RunResult {
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
            
            // Increase RANSAC threshold to avoid rejecting valid optical deformations in direct lens mode
            val ransacThresh = if (useRigidFallback) 15.0 else 5.0
            
            if (useRigidFallback) {
                if (matchedRef.size < 3) {
                     return V4RunResult(success = false, errorMessage = "Insufficient matched points (<3)", candidateMatches = matchedRef.size)
                }
                transformMat = Calib3d.estimateAffinePartial2D(srcMat, dstMat, mask, Calib3d.RANSAC, ransacThresh)
            } else {
                if (anchorRef.size < 4) {
                     return V4RunResult(success = false, errorMessage = "Insufficient anchors (<4)", candidateMatches = matchedRef.size)
                }
                transformMat = Calib3d.findHomography(srcMat, dstMat, Calib3d.RANSAC, ransacThresh, mask)
            }
            
            if (transformMat.empty()) {
                return V4RunResult(success = false, errorMessage = "Registration failed (empty transform)", candidateMatches = matchedRef.size)
            }
            
            val maskArray = ByteArray(mask.rows() * mask.cols())
            mask.get(0, 0, maskArray)
            inliersCount = maskArray.count { it.toInt() != 0 }
            
            val ptsToMeasureRef = if (useRigidFallback) matchedRef else measurementRef
            val ptsToMeasureLens = if (useRigidFallback) matchedLens else measurementLens
            
            if (ptsToMeasureRef.size < 6) {
                 return V4RunResult(success = false, errorMessage = "Insufficient measurement points (<6)", candidateMatches = matchedRef.size, acceptedMatches = inliersCount)
            }
            
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
            
            var sumDx = 0.0
            var sumDy = 0.0
            for (i in ptsToMeasureRef.indices) {
                sumDx += (transformedLens[i].x - ptsToMeasureRef[i].x)
                sumDy += (transformedLens[i].y - ptsToMeasureRef[i].y)
            }
            val meanDx = sumDx / ptsToMeasureRef.size
            val meanDy = sumDy / ptsToMeasureRef.size
            
            val A = Mat(ptsToMeasureRef.size, 3, CvType.CV_64F)
            val B = Mat(ptsToMeasureRef.size, 2, CvType.CV_64F)
            
            for (i in ptsToMeasureRef.indices) {
                A.put(i, 0, ptsToMeasureRef[i].x)
                A.put(i, 1, ptsToMeasureRef[i].y)
                A.put(i, 2, 1.0)
                
                B.put(i, 0, transformedLens[i].x - ptsToMeasureRef[i].x)
                B.put(i, 1, transformedLens[i].y - ptsToMeasureRef[i].y)
            }
            
            // NUMERICAL ROBUSTNESS CHECK
            val W = Mat()
            val U = Mat()
            val Vt = Mat()
            Core.SVDecomp(A, W, U, Vt)
            
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
                degeneracyStatus = "RANK_DEFICIENT_($rank)"
            } else if (cond > 1e4 || cond.isNaN()) {
                degeneracyStatus = "ILL_CONDITIONED_($cond)"
            }
            
            if (degeneracyStatus != "OK") {
                 return V4RunResult(success = false, errorMessage = "Degenerate geometric configuration: $degeneracyStatus",
                     candidateMatches = matchedRef.size, acceptedMatches = inliersCount, matrixRank = rank, conditionNumber = cond, degeneracyStatus = degeneracyStatus)
            }
            
            val J_matrix = Mat()
            try {
                Core.solve(A, B, J_matrix, Core.DECOMP_SVD)
            } catch (e: Exception) {
                return V4RunResult(success = false, errorMessage = "OpenCV solve failed: ${e.message}",
                     candidateMatches = matchedRef.size, acceptedMatches = inliersCount, matrixRank = rank, conditionNumber = cond, degeneracyStatus = "SOLVE_EXCEPTION")
            }
            
            // Validation of solved matrix
            val j00 = J_matrix.get(0, 0)[0]
            val j10 = J_matrix.get(0, 1)[0]
            val j01 = J_matrix.get(1, 0)[0]
            val j11 = J_matrix.get(1, 1)[0]
            
            if (j00.isNaN() || j10.isNaN() || j01.isNaN() || j11.isNaN() ||
                j00.isInfinite() || j10.isInfinite() || j01.isInfinite() || j11.isInfinite()) {
                return V4RunResult(success = false, errorMessage = "NaN/Infinity in optical field solution",
                     candidateMatches = matchedRef.size, acceptedMatches = inliersCount, matrixRank = rank, conditionNumber = cond, degeneracyStatus = "NAN_INF")
            }
            
            var fieldFitRmsSum = 0.0
            for (i in ptsToMeasureRef.indices) {
                val x = ptsToMeasureRef[i].x
                val y = ptsToMeasureRef[i].y
                val u = j00 * x + j01 * y + J_matrix.get(2, 0)[0]
                val v = j10 * x + j11 * y + J_matrix.get(2, 1)[0]
                
                val dx = transformedLens[i].x - ptsToMeasureRef[i].x
                val dy = transformedLens[i].y - ptsToMeasureRef[i].y
                
                val diffU = u - dx
                val diffV = v - dy
                fieldFitRmsSum += diffU * diffU + diffV * diffV
            }
            val fieldFitRms = sqrt(fieldFitRmsSum / ptsToMeasureRef.size)

            val s00 = j00
            val s11 = j11
            val s01 = 0.5 * (j01 + j10)
            
            val trace = s00 + s11
            val det = s00 * s11 - s01 * s01
            
            val lambda1 = trace / 2.0 + sqrt(max(0.0, (trace * trace) / 4.0 - det))
            val lambda2 = trace / 2.0 - sqrt(max(0.0, (trace * trace) / 4.0 - det))
            
            val dirX = lambda1 - s11
            val dirY = s01
            val angleRad = atan2(dirY, dirX)
            var axis = (angleRad * 180.0 / Math.PI)
            if (axis < 0) axis += 180.0
            if (axis >= 180.0) axis -= 180.0
            
            val isotropic = (lambda1 + lambda2) / 2.0
            val anisotropic = abs(lambda1 - lambda2)
            
            return V4RunResult(
                success = true,
                axis = axis,
                lambda1 = lambda1,
                lambda2 = lambda2,
                isotropic = isotropic,
                anisotropic = anisotropic,
                trackedDots = ptsToMeasureRef.size,
                registrationRms = registrationRms,
                ransacInliers = inliersCount,
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
                acceptedMatches = ptsToMeasureRef.size,
                rejectedMatches = matchedRef.size - ptsToMeasureRef.size,
                matrixRank = rank,
                conditionNumber = cond,
                degeneracyStatus = degeneracyStatus
            )
        } catch (e: Exception) {
            android.util.Log.e("V4OpticalAnalyzer", "AnalyzePoints failed", e)
            return V4RunResult(success = false, errorMessage = "Exception: ${e.message}", degeneracyStatus = "EXCEPTION")
        }
    }"""

content = re.sub(r'    fun analyzePoints\([\s\S]*?    \}', analyze_points_replacement, content, count=1)

# In `analyze()`, we need to call `analyzePoints` with `baseRefPoints.size` and `baseLensPoints.size`
analyze_call_old = """            val res = analyzePoints(matchedRef, matchedLens, w, h)"""
analyze_call_new = """            val res = analyzePoints(matchedRef, matchedLens, w, h, baseRefPoints.size, baseLensPoints.size)"""
content = content.replace(analyze_call_old, analyze_call_new)

# In `analyze()`, relax `if (matchedRef.size < 30)` to `if (matchedRef.size < 10)`
content = content.replace("if (matchedRef.size < 30)", "if (matchedRef.size < 10)")
content = content.replace("Matched dots < 30", "Matched dots < 10")

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)

