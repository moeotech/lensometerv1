import re

with open('analyze_points_end.txt', 'r') as f:
    original = f.read()

replacement = """            val ptsToMeasureLens = matchedLens.toMutableList()
            
            val srcMeasMat = MatOfPoint2f()
            srcMeasMat.fromList(ptsToMeasureLens)
            val dstMeasMat = MatOfPoint2f()
            
            Core.transform(srcMeasMat, dstMeasMat, transformMat)
            val transformedLens = dstMeasMat.toList()
            
            if (!useRigidFallback) {
                var rSum = 0.0
                val anchorLensMat = MatOfPoint2f().apply { fromList(anchorLens) }
                val anchorLensTransformed = MatOfPoint2f()
                Core.transform(anchorLensMat, anchorLensTransformed, transformMat)
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

            val opticalPairs = mutableListOf<OpticalPair>()
            for (i in matchedRef.indices) {
                opticalPairs.add(OpticalPair(
                    reference = matchedRef[i],
                    observed = transformedLens[i],
                    displacement = Point(transformedLens[i].x - matchedRef[i].x, transformedLens[i].y - matchedRef[i].y),
                    originalIndex = i
                ))
            }

            val searchRadius = spacing * 1.8
            val minNeighbors = 3
            
            val localResiduals = mutableListOf<Double>()

            // Task 4: Global Displacement Magnitude stats
            val globalMagnitudes = opticalPairs.map { hypot(it.displacement.x, it.displacement.y) }.sorted()
            var dispMedian = 0.0
            var dispMAD = 0.0
            var dispP90 = 0.0
            var dispMax = 0.0
            if (globalMagnitudes.isNotEmpty()) {
                dispMedian = globalMagnitudes[globalMagnitudes.size / 2]
                dispMAD = globalMagnitudes.map { abs(it - dispMedian) }.sorted()[globalMagnitudes.size / 2]
                dispP90 = globalMagnitudes[(globalMagnitudes.size * 0.9).toInt().coerceAtMost(globalMagnitudes.size - 1)]
                dispMax = globalMagnitudes.last()
            }

            for (i in opticalPairs.indices) {
                val pair = opticalPairs[i]
                
                // TASK 4: Reject extreme global magnitude
                val mag = hypot(pair.displacement.x, pair.displacement.y)
                if (mag > max(dispMedian + 5.0 * dispMAD, spacing)) {
                    pair.status = "GLOBAL_OUTLIER"
                    continue
                }

                val neighborIndices = mutableListOf<Int>()
                for (j in opticalPairs.indices) {
                    if (i == j) continue
                    val nPair = opticalPairs[j]
                    val distSq = (pair.reference.x - nPair.reference.x).pow(2) + (pair.reference.y - nPair.reference.y).pow(2)
                    if (distSq < searchRadius * searchRadius) {
                        neighborIndices.add(j)
                    }
                }
                
                if (neighborIndices.size < minNeighbors) {
                    // Not enough neighbors to verify, but we don't reject by default
                    continue
                }

                val nDispsX = neighborIndices.map { opticalPairs[it].displacement.x }.sorted()
                val nDispsY = neighborIndices.map { opticalPairs[it].displacement.y }.sorted()
                
                val medX = nDispsX[nDispsX.size / 2]
                val medY = nDispsY[nDispsY.size / 2]
                
                val nDistToMed = neighborIndices.map { 
                    hypot(opticalPairs[it].displacement.x - medX, opticalPairs[it].displacement.y - medY)
                }.sorted()
                val mad = nDistToMed[nDistToMed.size / 2]
                
                val distToMed = hypot(pair.displacement.x - medX, pair.displacement.y - medY)
                localResiduals.add(distToMed)
                
                val thresh = max(mad * 4.0, spacing * 0.15)
                if (distToMed > thresh) {
                    pair.status = "LOCAL_OUTLIER"
                    continue
                }

                var crossing = false
                for (j in neighborIndices) {
                    val nPair = opticalPairs[j]
                    
                    val refDist = hypot(pair.reference.x - nPair.reference.x, pair.reference.y - nPair.reference.y)
                    val obsDist = hypot(pair.observed.x - nPair.observed.x, pair.observed.y - nPair.observed.y)
                    
                    if (obsDist < refDist * 0.3) {
                        crossing = true
                        break
                    }
                    
                    val refVecX = nPair.reference.x - pair.reference.x
                    val refVecY = nPair.reference.y - pair.reference.y
                    val dstVecX = nPair.observed.x - pair.observed.x
                    val dstVecY = nPair.observed.y - pair.observed.y
                    
                    val dot = refVecX * dstVecX + refVecY * dstVecY
                    if (dot < 0) { 
                        crossing = true
                        break
                    }
                    
                    val ratio = obsDist / max(1e-5, refDist)
                    if (ratio > 3.0) {
                        crossing = true
                        break
                    }
                }
                
                if (crossing) {
                    pair.status = "CROSSING_REJECTED"
                }
            }
            
            val medianLocalRes = if (localResiduals.isNotEmpty()) localResiduals.sorted()[localResiduals.size / 2] else 0.0
            val madLocalRes = if (localResiduals.isNotEmpty()) {
                val m = medianLocalRes
                localResiduals.map { abs(it - m) }.sorted()[localResiduals.size / 2]
            } else 0.0

            val retainedPairs = opticalPairs.filter { it.status == "RETAINED" }
            
            val numMeas = retainedPairs.size
            if (numMeas < 6) {
                 return V4RunResult(success = false, errorMessage = "Insufficient measurement points (<6)", candidateMatches = matchedRef.size, acceptedMatches = inliersCount, matchRejections = rejections)
            }
            
            val A = Mat(numMeas, 3, CvType.CV_64F)
            val B = Mat(numMeas, 2, CvType.CV_64F)
            
            for (i in 0 until numMeas) {
                A.put(i, 0, retainedPairs[i].reference.x)
                A.put(i, 1, retainedPairs[i].reference.y)
                A.put(i, 2, 1.0)
                
                B.put(i, 0, retainedPairs[i].displacement.x)
                B.put(i, 1, retainedPairs[i].displacement.y)
            }
            
            val J_matrix = Mat(3, 2, CvType.CV_64F)
            val weights = DoubleArray(numMeas) { 1.0 }
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
                    val pt = retainedPairs[i].reference
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
                    
                    val dx = retainedPairs[i].displacement.x
                    val dy = retainedPairs[i].displacement.y
                    
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
            val wMat = Mat()
            Core.SVDecomp(AW_final, wMat, Mat(), Mat())
            var rank = 0
            var cond = 0.0
            val sv = DoubleArray(wMat.rows())
            if (!wMat.empty()) {
                for (i in 0 until wMat.rows()) {
                    val s = wMat.get(i, 0)[0]
                    sv[i] = s
                    if (s > 1e-5) rank++
                }
                cond = if (sv.last() > 1e-9) sv.first() / sv.last() else Double.MAX_VALUE
            }
            
            var degeneracyStatus = "OK"
            if (rank < 3 || cond > 5000.0) {
                degeneracyStatus = "DEGENERATE (rank=$rank, cond=${String.format("%.1f", cond)})"
            }
            
            val J_mat = Mat(2, 2, CvType.CV_64F)
            J_mat.put(0, 0, j00, j01)
            J_mat.put(1, 0, j10, j11)
            
            val eVal = Mat()
            val eVec = Mat()
            Core.eigen(J_mat, eVal, eVec)
            
            var l1 = 0.0
            var l2 = 0.0
            if (eVal.rows() >= 2) {
                l1 = eVal.get(0, 0)[0]
                l2 = eVal.get(1, 0)[0]
            }
            
            if (Math.abs(l2) > Math.abs(l1)) {
                val temp = l1
                l1 = l2
                l2 = temp
            }
            
            val iso = (l1 + l2) / 2.0
            val aniso = l1 - l2
            
            val J_sym = Mat(2, 2, CvType.CV_64F)
            J_sym.put(0, 0, j00)
            J_sym.put(0, 1, (j01 + j10) / 2.0)
            J_sym.put(1, 0, (j01 + j10) / 2.0)
            J_sym.put(1, 1, j11)
            
            val eValSym = Mat()
            val eVecSym = Mat()
            Core.eigen(J_sym, eValSym, eVecSym)
            
            var axisDeg = 0.0
            if (eVecSym.rows() >= 2 && eVecSym.cols() >= 2) {
                val vx = eVecSym.get(0, 0)[0]
                val vy = eVecSym.get(0, 1)[0]
                axisDeg = atan2(vy, vx) * 180.0 / Math.PI
            }
            
            while (axisDeg < 0.0) axisDeg += 180.0
            while (axisDeg >= 180.0) axisDeg -= 180.0
            
            var sumDx = 0.0; var sumDy = 0.0
            for (i in 0 until numMeas) {
                sumDx += retainedPairs[i].displacement.x
                sumDy += retainedPairs[i].displacement.y
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
                referencePoints = opticalPairs.map { it.reference },
                observedPoints = opticalPairs.map { it.observed },
                localOutlierRejections = opticalPairs.count { it.status == "LOCAL_OUTLIER" },
                crossingVectorRejections = opticalPairs.count { it.status == "CROSSING_REJECTED" },
                medianLocalResidual = medianLocalRes,
                madLocalResidual = madLocalRes,
                opticalRejectedReferencePoints = opticalPairs.filter { it.status != "RETAINED" }.map { it.reference },
                opticalRejectedObservedPoints = opticalPairs.filter { it.status != "RETAINED" }.map { it.observed },
                refWidth = w.toInt(),
                refHeight = h.toInt(),
                registrationModel = registrationModel,
                registrationRotationDeg = registrationRotationDeg,
                registrationTx = registrationTx,
                registrationTy = registrationTy,
                registrationScale = 1.0,
                candidateMatches = matchedRef.size,
                acceptedMatches = opticalFieldRetainedCount,
                matchRejections = rejections,
                spatialCoveragePct = spatialCoveragePct,
                quadrantCoverage = quadCount,
                matrixRank = rank,
                conditionNumber = cond,
                degeneracyStatus = degeneracyStatus
            )"""
            
pattern = r'val ptsToMeasureLens = matchedLens\.toMutableList\(\).*?degeneracyStatus = degeneracyStatus\n\s*\)'

new_content = re.sub(pattern, replacement, original, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    full_content = f.read()
    
full_content = re.sub(pattern, replacement, full_content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(full_content)
