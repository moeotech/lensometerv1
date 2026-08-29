import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# We will extract the core logic into a public function that can be tested.
# Specifically, from `// 4. Registration (Remove global camera motion)` to the end of analyze()

core_logic = """    fun analyzePoints(matchedRef: List<Point>, matchedLens: List<Point>, w: Double, h: Double): V4RunResult {
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
            if (useRigidFallback) {
                transformMat = Calib3d.estimateAffinePartial2D(srcMat, dstMat, mask, Calib3d.RANSAC, 3.0)
            } else {
                transformMat = Calib3d.findHomography(srcMat, dstMat, Calib3d.RANSAC, 3.0, mask)
            }
            
            if (transformMat.empty()) {
                return V4RunResult(success = false, errorMessage = "Registration failed")
            }
            
            val maskArray = ByteArray(mask.rows() * mask.cols())
            mask.get(0, 0, maskArray)
            inliersCount = maskArray.count { it.toInt() != 0 }
            
            val ptsToMeasureRef = if (useRigidFallback) matchedRef else measurementRef
            val ptsToMeasureLens = if (useRigidFallback) matchedLens else measurementLens
            
            if (ptsToMeasureRef.isEmpty()) {
                 return V4RunResult(success = false, errorMessage = "No measurement points")
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
            
            val J_matrix = Mat()
            Core.solve(A, B, J_matrix, Core.DECOMP_SVD)
            
            val j00 = J_matrix.get(0, 0)[0]
            val j10 = J_matrix.get(0, 1)[0]
            val j01 = J_matrix.get(1, 0)[0]
            val j11 = J_matrix.get(1, 1)[0]
            
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
                refDotCount = matchedRef.size,
                lensDotCount = matchedLens.size,
                meanDx = meanDx,
                meanDy = meanDy,
                referencePoints = ptsToMeasureRef,
                observedPoints = transformedLens,
                refWidth = w.toInt(),
                refHeight = h.toInt(),
                globalScaleAmbiguous = globalScaleAmbiguous
            )
        } catch (e: Exception) {
            Log.e("V4OpticalAnalyzer", "AnalyzePoints failed", e)
            return V4RunResult(success = false, errorMessage = "Exception: ${e.message}")
        }
    }
"""

# Replace the body of analyze with a call to analyzePoints
replacement_body = """            if (matchedRef.size < 30) {
                return@withContext V4RunResult(success = false, errorMessage = "Matched dots < 30 (${matchedRef.size})")
            }

            val w = noLensFrames[0].width.toDouble()
            val h = noLensFrames[0].height.toDouble()
            
            val res = analyzePoints(matchedRef, matchedLens, w, h)
            if (!res.success) return@withContext res
            
            return@withContext res.copy(
                framesCaptured = refAgg.framesCaptured + lensAgg.framesCaptured,
                framesAccepted = refAgg.framesAccepted + lensAgg.framesAccepted,
                framesRejected = refAgg.framesRejected + lensAgg.framesRejected,
                refDotCount = baseRefPoints.size,
                lensDotCount = baseLensPoints.size
            )
        } catch (e: Exception) {
            Log.e("V4OpticalAnalyzer", "Analyze failed", e)
            return@withContext V4RunResult(success = false, errorMessage = "Exception: ${e.message}")
        }
    }"""

content = re.sub(r'            if \(matchedRef\.size < 30\) \{[\s\S]*?            return@withContext V4RunResult\(success = false, errorMessage = "Exception: \$\{e\.message\}"\)\n        \}\n    \}', replacement_body, content)

content = content.replace("object V4OpticalAnalyzer {", "object V4OpticalAnalyzer {\n" + core_logic)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)

