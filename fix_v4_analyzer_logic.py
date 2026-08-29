import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Replace the body of V4OpticalAnalyzer with the new logic

new_analyzer = """object V4OpticalAnalyzer {
    
    suspend fun analyze(noLensFrames: List<Bitmap>, withLensFrames: List<Bitmap>): V4RunResult = withContext(Dispatchers.Default) {
        if (noLensFrames.isEmpty() || withLensFrames.isEmpty()) {
            return@withContext V4RunResult(success = false, errorMessage = "Missing frames")
        }
        
        try {
            // 1. Reference Model (median/sub-pixel locations)
            val refAgg = aggregateFrames(noLensFrames)
            if (!refAgg.success) {
                return@withContext V4RunResult(success = false, errorMessage = "Ref aggregation failed: ${refAgg.errorMessage}")
            }
            val baseRefPoints = refAgg.points
            
            // 2. Lens Model
            val lensAgg = aggregateFrames(withLensFrames)
            if (!lensAgg.success) {
                return@withContext V4RunResult(success = false, errorMessage = "Lens aggregation failed: ${lensAgg.errorMessage}")
            }
            val baseLensPoints = lensAgg.points
            
            // 3. Match dots between ref and lens (Mutual nearest neighbor)
            val matchedRef = mutableListOf<Point>()
            val matchedLens = mutableListOf<Point>()
            
            for (pt1 in baseRefPoints) {
                var bestDist1 = Double.MAX_VALUE
                var bestPt2: Point? = null
                for (pt2 in baseLensPoints) {
                    val dist = hypot(pt1.x - pt2.x, pt1.y - pt2.y)
                    if (dist < bestDist1 && dist < 100.0) {
                        bestDist1 = dist
                        bestPt2 = pt2
                    }
                }
                
                if (bestPt2 != null) {
                    var bestDist2 = Double.MAX_VALUE
                    var bestPt1: Point? = null
                    for (pt1_check in baseRefPoints) {
                        val dist = hypot(pt1_check.x - bestPt2.x, pt1_check.y - bestPt2.y)
                        if (dist < bestDist2 && dist < 100.0) {
                            bestDist2 = dist
                            bestPt1 = pt1_check
                        }
                    }
                    if (bestPt1 == pt1) {
                        matchedRef.add(pt1)
                        matchedLens.add(bestPt2)
                    }
                }
            }
            
            if (matchedRef.size < 30) {
                return@withContext V4RunResult(success = false, errorMessage = "Matched dots < 30 (${matchedRef.size})")
            }

            // 4. Registration (Remove global camera motion)
            val w = noLensFrames[0].width.toDouble()
            val h = noLensFrames[0].height.toDouble()
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
            val finalRef = mutableListOf<Point>()
            val finalLensTransform = mutableListOf<Point>()
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
            var transformMat: Mat
            if (useRigidFallback) {
                // Estimate rigid transform (translation + rotation) -> partial affine
                // OpenCV's estimateAffinePartial2D includes scale. We just use it but flag it ambiguous
                transformMat = Calib3d.estimateAffinePartial2D(srcMat, dstMat, mask, Calib3d.RANSAC, 3.0)
            } else {
                transformMat = Calib3d.findHomography(srcMat, dstMat, Calib3d.RANSAC, 3.0, mask)
            }
            
            if (transformMat.empty()) {
                return@withContext V4RunResult(success = false, errorMessage = "Registration failed")
            }
            
            val maskArray = ByteArray(mask.rows() * mask.cols())
            mask.get(0, 0, maskArray)
            inliersCount = maskArray.count { it.toInt() != 0 }
            
            // Apply transformation to measurement points (or all points if fallback)
            val ptsToMeasureRef = if (useRigidFallback) matchedRef else measurementRef
            val ptsToMeasureLens = if (useRigidFallback) matchedLens else measurementLens
            
            if (ptsToMeasureRef.isEmpty()) {
                 return@withContext V4RunResult(success = false, errorMessage = "No measurement points")
            }
            
            val srcMeasMat = MatOfPoint2f()
            srcMeasMat.fromList(ptsToMeasureLens)
            val dstMeasMat = MatOfPoint2f()
            
            if (useRigidFallback) {
                // it's 2x3
                Core.transform(srcMeasMat, dstMeasMat, transformMat)
            } else {
                // it's 3x3
                Core.perspectiveTransform(srcMeasMat, dstMeasMat, transformMat)
            }
            
            val transformedLens = dstMeasMat.toList()
            
            // Calculate RMS of registration on anchors
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
            
            // 5. Fit Smooth 2D Deformation Field & Jacobian on MEASUREMENT points
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
            
            return@withContext V4RunResult(
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
                refDotCount = baseRefPoints.size,
                lensDotCount = baseLensPoints.size,
                meanDx = meanDx,
                meanDy = meanDy,
                referencePoints = ptsToMeasureRef,
                observedPoints = transformedLens,
                refWidth = noLensFrames[0].width,
                refHeight = noLensFrames[0].height,
                globalScaleAmbiguous = globalScaleAmbiguous,
                framesCaptured = refAgg.framesCaptured + lensAgg.framesCaptured,
                framesAccepted = refAgg.framesAccepted + lensAgg.framesAccepted,
                framesRejected = refAgg.framesRejected + lensAgg.framesRejected
            )

        } catch (e: Exception) {
            Log.e("V4OpticalAnalyzer", "Analyze failed", e)
            return@withContext V4RunResult(success = false, errorMessage = "Exception: ${e.message}")
        }
    }
    
    class AggResult(val success: Boolean, val errorMessage: String = "", val points: List<Point> = emptyList(), val framesCaptured: Int = 0, val framesAccepted: Int = 0, val framesRejected: Int = 0)
    
    private fun aggregateFrames(frames: List<Bitmap>): AggResult {
        if (frames.isEmpty()) return AggResult(false, "No frames")
        
        val allKeypoints = frames.map { detectDots(it) }
        val baseIdx = allKeypoints.indices.maxByOrNull { allKeypoints[it].size } ?: 0
        val basePoints = allKeypoints[baseIdx]
        
        if (basePoints.size < 10) return AggResult(false, "Not enough points in base frame")
        
        val baseMat = MatOfPoint2f()
        baseMat.fromList(basePoints)
        
        val pointGroups = Array(basePoints.size) { mutableListOf<Point>() }
        
        var accepted = 0
        var rejected = 0
        
        for (i in frames.indices) {
            val pts = allKeypoints[i]
            if (pts.size < 10) {
                rejected++
                continue
            }
            
            // Match with base using mutual nearest neighbor
            val matchedBase = mutableListOf<Point>()
            val matchedCurr = mutableListOf<Point>()
            val matchedBaseIndices = mutableListOf<Int>()
            
            for (j in basePoints.indices) {
                val pt1 = basePoints[j]
                var bestDist1 = Double.MAX_VALUE
                var bestPt2: Point? = null
                for (pt2 in pts) {
                    val dist = hypot(pt1.x - pt2.x, pt1.y - pt2.y)
                    if (dist < bestDist1 && dist < 100.0) {
                        bestDist1 = dist
                        bestPt2 = pt2
                    }
                }
                
                if (bestPt2 != null) {
                    var bestDist2 = Double.MAX_VALUE
                    var bestPt1: Point? = null
                    for (pt1_check in basePoints) {
                        val dist = hypot(pt1_check.x - bestPt2.x, pt1_check.y - bestPt2.y)
                        if (dist < bestDist2 && dist < 100.0) {
                            bestDist2 = dist
                            bestPt1 = pt1_check
                        }
                    }
                    if (bestPt1 == pt1) {
                        matchedBase.add(pt1)
                        matchedCurr.add(bestPt2)
                        matchedBaseIndices.add(j)
                    }
                }
            }
            
            if (matchedBase.size < 10) {
                rejected++
                continue
            }
            
            val srcMat = MatOfPoint2f()
            srcMat.fromList(matchedCurr)
            val dstMat = MatOfPoint2f()
            dstMat.fromList(matchedBase)
            
            val mask = Mat()
            val transform = Calib3d.estimateAffinePartial2D(srcMat, dstMat, mask, Calib3d.RANSAC, 3.0)
            
            if (transform.empty()) {
                rejected++
                continue
            }
            
            val maskArray = ByteArray(mask.rows() * mask.cols())
            mask.get(0, 0, maskArray)
            val inliers = maskArray.count { it.toInt() != 0 }
            if (inliers < 10) {
                rejected++
                continue
            }
            
            val allPtsMat = MatOfPoint2f()
            allPtsMat.fromList(pts)
            val transformedPtsMat = MatOfPoint2f()
            Core.transform(allPtsMat, transformedPtsMat, transform)
            val transformedPts = transformedPtsMat.toList()
            
            accepted++
            
            // Map back to base points
            for (pt in transformedPts) {
                var bestDist = Double.MAX_VALUE
                var bestIdx = -1
                for (j in basePoints.indices) {
                    val bPt = basePoints[j]
                    val dist = hypot(pt.x - bPt.x, pt.y - bPt.y)
                    if (dist < bestDist && dist < 5.0) {
                        bestDist = dist
                        bestIdx = j
                    }
                }
                if (bestIdx != -1) {
                    pointGroups[bestIdx].add(pt)
                }
            }
        }
        
        val finalPoints = mutableListOf<Point>()
        for (group in pointGroups) {
            if (group.size > frames.size * 0.3) {
                group.sortBy { it.x }
                val medianX = group[group.size / 2].x
                group.sortBy { it.y }
                val medianY = group[group.size / 2].y
                
                // Optional: MAD outlier rejection
                val madX = group.map { abs(it.x - medianX) }.sorted()[group.size / 2] * 1.4826
                val madY = group.map { abs(it.y - medianY) }.sorted()[group.size / 2] * 1.4826
                
                var sumX = 0.0
                var sumY = 0.0
                var count = 0
                for (pt in group) {
                    if (abs(pt.x - medianX) <= 3 * madX && abs(pt.y - medianY) <= 3 * madY) {
                        sumX += pt.x
                        sumY += pt.y
                        count++
                    }
                }
                if (count > 0) {
                    finalPoints.add(Point(sumX / count, sumY / count))
                }
            }
        }
        
        return AggResult(true, "", finalPoints, frames.size, accepted, rejected)
    }

    private fun detectDots(bitmap: Bitmap): List<Point> {
        val mat = Mat()
        Utils.bitmapToMat(bitmap, mat)
        val gray = Mat()
        Imgproc.cvtColor(mat, gray, Imgproc.COLOR_BGR2GRAY)
        
        // Adaptive threshold
        val thresh = Mat()
        Imgproc.adaptiveThreshold(gray, thresh, 255.0, Imgproc.ADAPTIVE_THRESH_GAUSSIAN_C, Imgproc.THRESH_BINARY_INV, 11, 2.0)
        
        // Find contours
        val contours = mutableListOf<MatOfPoint>()
        val hierarchy = Mat()
        Imgproc.findContours(thresh, contours, hierarchy, Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_SIMPLE)
        
        val points = mutableListOf<Point>()
        for (contour in contours) {
            val area = Imgproc.contourArea(contour)
            if (area > 10.0 && area < 500.0) { // Area filter
                val moments = Imgproc.moments(contour)
                if (moments.m00 != 0.0) {
                    val cx = moments.m10 / moments.m00
                    val cy = moments.m01 / moments.m00
                    points.add(Point(cx, cy))
                }
            }
        }
        
        mat.release()
        gray.release()
        thresh.release()
        hierarchy.release()
        
        return points
    }

    suspend fun calculateRepeatability(results: List<V4RunResult>): V4Result = withContext(Dispatchers.Default) {
        if (results.size < 3) {
            return@withContext V4Result(success = false, errorMessage = "Need 3 runs")
        }
        
        if (results.any { !it.success }) {
            return@withContext V4Result(success = false, errorMessage = "One or more runs failed: " + results.first { !it.success }.errorMessage)
        }
        
        val lambda1Mean = results.map { it.lambda1 }.average()
        val lambda2Mean = results.map { it.lambda2 }.average()
        val isotropicMean = results.map { it.isotropic }.average()
        val anisotropicMean = results.map { it.anisotropic }.average()
        
        val lambda1Std = sqrt(results.map { (it.lambda1 - lambda1Mean) * (it.lambda1 - lambda1Mean) }.average())
        val lambda2Std = sqrt(results.map { (it.lambda2 - lambda2Mean) * (it.lambda2 - lambda2Mean) }.average())
        val isotropicStd = sqrt(results.map { (it.isotropic - isotropicMean) * (it.isotropic - isotropicMean) }.average())
        val anisotropicStd = sqrt(results.map { (it.anisotropic - anisotropicMean) * (it.anisotropic - anisotropicMean) }.average())
        
        // Circular mean for axis
        var sinSum = 0.0
        var cosSum = 0.0
        for (r in results) {
            val rad = r.axis * 2.0 * Math.PI / 180.0
            sinSum += sin(rad)
            cosSum += cos(rad)
        }
        var axisMean = atan2(sinSum / results.size, cosSum / results.size) * 180.0 / (2.0 * Math.PI)
        if (axisMean < 0) axisMean += 180.0
        if (axisMean >= 180.0) axisMean -= 180.0
        
        val lastRun = results.last()
        
        // Draw Vector Map
        val visualVectorMap = if (lastRun.referencePoints.isNotEmpty()) {
             drawVectorMapInternal(lastRun, 1f)
        } else null
        
        return@withContext V4Result(
            success = true,
            sphDisplay = "NOT CALIBRATED",
            cylDisplay = "NOT CALIBRATED",
            axisDisplay = String.format("%.0f", axisMean),
            lambda1 = lambda1Mean,
            lambda2 = lambda2Mean,
            isotropic = isotropicMean,
            anisotropic = anisotropicMean,
            lambda1Std = lambda1Std,
            lambda2Std = lambda2Std,
            isotropicStd = isotropicStd,
            anisotropicStd = anisotropicStd,
            allRuns = results,
            trackedDots = lastRun.trackedDots,
            registrationRms = lastRun.registrationRms,
            ransacInliers = lastRun.ransacInliers,
            fieldFitRms = lastRun.fieldFitRms,
            refDotCount = lastRun.refDotCount,
            lensDotCount = lastRun.lensDotCount,
            meanDx = lastRun.meanDx,
            meanDy = lastRun.meanDy,
            visualVectorMap = visualVectorMap,
            lastRunResult = lastRun,
            globalScaleAmbiguous = results.any { it.globalScaleAmbiguous }
        )
    }
    
    fun drawVectorMap(result: V4Result, mag: Float): Bitmap? {
        if (result.lastRunResult == null) return null
        return drawVectorMapInternal(result.lastRunResult, mag)
    }
    
    private fun drawVectorMapInternal(run: V4RunResult, mag: Float): Bitmap {
        val bitmap = Bitmap.createBitmap(run.refWidth, run.refHeight, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        canvas.drawColor(Color.BLACK)
        
        val paintRef = Paint().apply { color = Color.RED; style = Paint.Style.FILL; isAntiAlias = true }
        val paintLens = Paint().apply { color = Color.GREEN; style = Paint.Style.FILL; isAntiAlias = true }
        val paintArrow = Paint().apply { color = Color.YELLOW; strokeWidth = 2f; style = Paint.Style.STROKE; isAntiAlias = true }
        
        for (i in run.referencePoints.indices) {
            val refPt = run.referencePoints[i]
            val lensPt = run.observedPoints[i]
            
            canvas.drawCircle(refPt.x.toFloat(), refPt.y.toFloat(), 3f, paintRef)
            
            val dx = (lensPt.x - refPt.x) * mag
            val dy = (lensPt.y - refPt.y) * mag
            
            canvas.drawCircle((refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), 3f, paintLens)
            canvas.drawLine(refPt.x.toFloat(), refPt.y.toFloat(), (refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), paintArrow)
        }
        
        return bitmap
    }
}"""

content = re.sub(r'object V4OpticalAnalyzer \{[\s\S]*\}', new_analyzer, content, count=1)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)

