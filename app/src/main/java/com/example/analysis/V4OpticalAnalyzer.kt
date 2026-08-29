package com.example.analysis

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.Log
import org.opencv.android.Utils
import org.opencv.calib3d.Calib3d
import org.opencv.core.*
import org.opencv.imgproc.Imgproc
import kotlin.math.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class V4Result(
    val success: Boolean,
    val errorMessage: String = "",
    val sphDisplay: String = "",
    val cylDisplay: String = "",
    val axisDisplay: String = "",
    val p1: Double = 0.0,
    val p2: Double = 0.0,
    val sphStd: Double = 0.0,
    val cylStd: Double = 0.0,
    val p1Std: Double = 0.0,
    val p2Std: Double = 0.0,
    val allRuns: List<V4RunResult> = emptyList(),
    val anisotropy: Double = 0.0,
    val isotropic: Double = 0.0,
    val trackedDots: Int = 0,
    val registrationRms: Double = 0.0,
    val ransacInliers: Int = 0,
    val fieldFitRms: Double = 0.0,
    val refDotCount: Int = 0,
    val lensDotCount: Int = 0,
    val meanDx: Double = 0.0,
    val meanDy: Double = 0.0,
    val lambda1: Double = 0.0,
    val lambda2: Double = 0.0,
    val visualVectorMap: Bitmap? = null,
    val lastRunResult: V4RunResult? = null
)

data class V4RunResult(
    val success: Boolean,
    val errorMessage: String = "",
    val sph: Double = 0.0,
    val cyl: Double = 0.0,
    val axis: Double = 0.0,
    val p1: Double = 0.0,
    val p2: Double = 0.0,
    val sphStd: Double = 0.0,
    val cylStd: Double = 0.0,
    val p1Std: Double = 0.0,
    val p2Std: Double = 0.0,
    val allRuns: List<V4RunResult> = emptyList(),
    val lambda1: Double = 0.0,
    val lambda2: Double = 0.0,
    val trackedDots: Int = 0,
    val registrationRms: Double = 0.0,
    val ransacInliers: Int = 0,
    val fieldFitRms: Double = 0.0,
    val refDotCount: Int = 0,
    val lensDotCount: Int = 0,
    val meanDx: Double = 0.0,
    val meanDy: Double = 0.0,
    val referencePoints: List<Point> = emptyList(),
    val observedPoints: List<Point> = emptyList(),
    val refWidth: Int = 0,
    val refHeight: Int = 0
)

object V4OpticalAnalyzer {
    
    suspend fun analyze(noLensFrames: List<Bitmap>, withLensFrames: List<Bitmap>): V4RunResult = withContext(Dispatchers.Default) {
        if (noLensFrames.isEmpty() || withLensFrames.isEmpty()) {
            return@withContext V4RunResult(success = false, errorMessage = "Missing frames")
        }
        
        try {
            // 1. Reference Model (median/sub-pixel locations)
            val refKeypointsAllFrames = mutableListOf<List<Point>>()
            for (frame in noLensFrames) {
                refKeypointsAllFrames.add(detectDots(frame))
            }
            // For simplicity, just use the first frame for the reference if it has enough points, or combine.
            // A true median tracking across 30 frames is complex without tracking. 
            // We'll use the frame with the most points as our base reference.
            val baseRefIdx = refKeypointsAllFrames.indices.maxByOrNull { refKeypointsAllFrames[it].size } ?: 0
            val baseRefPoints = refKeypointsAllFrames[baseRefIdx]
            
            if (baseRefPoints.size < 50) {
                return@withContext V4RunResult(success = false, errorMessage = "Insufficient reference dots (${baseRefPoints.size} < 50)")
            }
            
            // 2. Lens Model (detect dots in lens frames)
            val lensKeypointsAllFrames = mutableListOf<List<Point>>()
            for (frame in withLensFrames) {
                lensKeypointsAllFrames.add(detectDots(frame))
            }
            val baseLensIdx = lensKeypointsAllFrames.indices.maxByOrNull { lensKeypointsAllFrames[it].size } ?: 0
            val baseLensPoints = lensKeypointsAllFrames[baseLensIdx]
            
            if (baseLensPoints.size < 50) {
                return@withContext V4RunResult(success = false, errorMessage = "Insufficient lens dots (${baseLensPoints.size} < 50)")
            }

            // 3. Match dots between ref and lens (nearest neighbor or robust matching)
            val matchedRef = mutableListOf<Point>()
            val matchedLens = mutableListOf<Point>()
            
            for (pt1 in baseRefPoints) {
                var bestDist = Double.MAX_VALUE
                var bestPt2: Point? = null
                for (pt2 in baseLensPoints) {
                    val dist = hypot(pt1.x - pt2.x, pt1.y - pt2.y)
                    if (dist < bestDist && dist < 100.0) { // arbitrary threshold for matching
                        bestDist = dist
                        bestPt2 = pt2
                    }
                }
                if (bestPt2 != null) {
                    matchedRef.add(pt1)
                    matchedLens.add(bestPt2)
                }
            }
            
            if (matchedRef.size < 50) {
                return@withContext V4RunResult(success = false, errorMessage = "Matched dots < 50 (${matchedRef.size})")
            }

            // 4. Registration (Remove global camera motion)
            val refMat = MatOfPoint2f()
            refMat.fromList(matchedRef)
            val lensMat = MatOfPoint2f()
            lensMat.fromList(matchedLens)
            
            val mask = Mat()
            val homography = Calib3d.findHomography(lensMat, refMat, Calib3d.RANSAC, 3.0, mask)
            
            if (homography.empty()) {
                return@withContext V4RunResult(success = false, errorMessage = "Homography failed")
            }
            
            var inliers = 0
            val maskArray = ByteArray(mask.rows() * mask.cols())
            mask.get(0, 0, maskArray)
            
            val inlierRef = mutableListOf<Point>()
            val inlierLensTransformed = mutableListOf<Point>()
            
            for (i in maskArray.indices) {
                if (maskArray[i].toInt() != 0) {
                    inliers++
                    inlierRef.add(matchedRef[i])
                    val originalLensPt = matchedLens[i]
                    // Transform lens point by homography
                    val src = MatOfPoint2f(originalLensPt)
                    val dst = MatOfPoint2f()
                    Core.perspectiveTransform(src, dst, homography)
                    inlierLensTransformed.add(dst.toList()[0])
                }
            }
            
            if (inliers < 50) {
                return@withContext V4RunResult(success = false, errorMessage = "RANSAC inliers < 50 ($inliers)")
            }
            
            // Calculate Registration RMS (how well did homography align the points overall?)
            var rmsSum = 0.0
            for (i in inlierRef.indices) {
                val dx = inlierLensTransformed[i].x - inlierRef[i].x
                val dy = inlierLensTransformed[i].y - inlierRef[i].y
                rmsSum += dx * dx + dy * dy
            }
            val registrationRms = sqrt(rmsSum / inlierRef.size)
            
            if (registrationRms > 10.0) { // Threshold
                 return@withContext V4RunResult(success = false, errorMessage = "Registration RMS too high ($registrationRms)")
            }

            // 5. Fit Smooth 2D Deformation Field & Jacobian
            var sumDx = 0.0
            var sumDy = 0.0
            for (i in inlierRef.indices) {
                sumDx += (inlierLensTransformed[i].x - inlierRef[i].x)
                sumDy += (inlierLensTransformed[i].y - inlierRef[i].y)
            }
            val meanDx = sumDx / inlierRef.size
            val meanDy = sumDy / inlierRef.size
            
            // To find Jacobian J:
            // u = J00*x + J01*y + c0
            // v = J10*x + J11*y + c1
            // Use least squares.
            val A = Mat(inlierRef.size, 3, CvType.CV_64F)
            val B = Mat(inlierRef.size, 2, CvType.CV_64F)
            
            for (i in inlierRef.indices) {
                A.put(i, 0, inlierRef[i].x)
                A.put(i, 1, inlierRef[i].y)
                A.put(i, 2, 1.0)
                
                B.put(i, 0, inlierLensTransformed[i].x - inlierRef[i].x)
                B.put(i, 1, inlierLensTransformed[i].y - inlierRef[i].y)
            }
            
            val J_matrix = Mat()
            Core.solve(A, B, J_matrix, Core.DECOMP_SVD)
            // J_matrix is 3x2: 
            // row 0: J00, J10
            // row 1: J01, J11
            // row 2: c0, c1
            
            val j00 = J_matrix.get(0, 0)[0]
            val j10 = J_matrix.get(0, 1)[0]
            val j01 = J_matrix.get(1, 0)[0]
            val j11 = J_matrix.get(1, 1)[0]
            
            // Calculate field fit RMS
            var fieldFitRmsSum = 0.0
            for (i in inlierRef.indices) {
                val x = inlierRef[i].x
                val y = inlierRef[i].y
                val u = j00 * x + j01 * y + J_matrix.get(2, 0)[0]
                val v = j10 * x + j11 * y + J_matrix.get(2, 1)[0]
                
                val dx = inlierLensTransformed[i].x - inlierRef[i].x
                val dy = inlierLensTransformed[i].y - inlierRef[i].y
                
                val diffU = u - dx
                val diffV = v - dy
                fieldFitRmsSum += diffU * diffU + diffV * diffV
            }
            val fieldFitRms = sqrt(fieldFitRmsSum / inlierRef.size)
            if (fieldFitRms > 5.0) {
                return@withContext V4RunResult(success = false, errorMessage = "Field fit unstable ($fieldFitRms)")
            }

            // Symmetric component
            val s00 = j00
            val s11 = j11
            val s01 = 0.5 * (j01 + j10)
            
            // Eigen decomposition of S = [s00, s01; s01, s11]
            // trace = s00 + s11
            // det = s00*s11 - s01*s01
            val trace = s00 + s11
            val det = s00 * s11 - s01 * s01
            
            val lambda1 = trace / 2.0 + sqrt((trace * trace) / 4.0 - det)
            val lambda2 = trace / 2.0 - sqrt((trace * trace) / 4.0 - det)
            
            // Principal direction for lambda1
            val dirX = lambda1 - s11
            val dirY = s01
            val angleRad = atan2(dirY, dirX)
            var axis = (angleRad * 180.0 / Math.PI)
            if (axis < 0) axis += 180.0
            if (axis >= 180.0) axis -= 180.0
            
            // Convert to arbitrary 'power' (requires calibration)
            val p1 = lambda1 * 100.0 // Arbitrary scale for now
            val p2 = lambda2 * 100.0
            
            // Minus cylinder convention
            val sph = max(p1, p2)
            val cyl = min(p1, p2) - sph
            val finalAxis = if (p1 > p2) axis else (axis + 90) % 180
            
            return@withContext V4RunResult(
                success = true,
                sph = sph,
                cyl = cyl,
                axis = finalAxis,
                p1 = p1,
                p2 = p2,
                lambda1 = lambda1,
                lambda2 = lambda2,
                trackedDots = inlierRef.size,
                registrationRms = registrationRms,
                ransacInliers = inliers,
                fieldFitRms = fieldFitRms,
                refDotCount = baseRefPoints.size,
                lensDotCount = baseLensPoints.size,
                meanDx = meanDx,
                meanDy = meanDy,
                referencePoints = inlierRef,
                observedPoints = inlierLensTransformed,
                refWidth = noLensFrames[0].width,
                refHeight = noLensFrames[0].height
            )

        } catch (e: Exception) {
            return@withContext V4RunResult(success = false, errorMessage = "Exception: ${e.message}")
        }
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
                val cx = moments.m10 / moments.m00
                val cy = moments.m01 / moments.m00
                points.add(Point(cx, cy))
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
        
        val sphMean = results.map { it.sph }.average()
        val cylMean = results.map { it.cyl }.average()
        val p1Mean = results.map { it.p1 }.average()
        val p2Mean = results.map { it.p2 }.average()
        val sphStd = sqrt(results.map { (it.sph - sphMean) * (it.sph - sphMean) }.average())
        val cylStd = sqrt(results.map { (it.cyl - cylMean) * (it.cyl - cylMean) }.average())
        
        
        val p1Std = sqrt(results.map { (it.p1 - p1Mean) * (it.p1 - p1Mean) }.average())
        val p2Std = sqrt(results.map { (it.p2 - p2Mean) * (it.p2 - p2Mean) }.average())
        
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
        
        
        
        val anisotropy = abs(p1Mean - p2Mean)
        val isotropic = (p1Mean + p2Mean) / 2.0
        
        val lastRun = results.last()
        
        // Draw Vector Map
        val visualVectorMap = if (lastRun.referencePoints.isNotEmpty()) {
             drawVectorMapInternal(lastRun, 1f)
        } else null
        
        return@withContext V4Result(
            success = true,
            sphDisplay = "NOT CALIBRATED", // Explicitly uncalibrated per instructions
            cylDisplay = "NOT CALIBRATED",
            axisDisplay = String.format("%.0f", axisMean),
            p1 = p1Mean,
            p2 = p2Mean,
            sphStd = sphStd,
            cylStd = cylStd,
            p1Std = p1Std,
            p2Std = p2Std,
            allRuns = results,
            anisotropy = anisotropy,
            isotropic = isotropic,
            trackedDots = lastRun.trackedDots,
            registrationRms = lastRun.registrationRms,
            ransacInliers = lastRun.ransacInliers,
            fieldFitRms = lastRun.fieldFitRms,
            refDotCount = lastRun.refDotCount,
            lensDotCount = lastRun.lensDotCount,
            meanDx = lastRun.meanDx,
            meanDy = lastRun.meanDy,
            lambda1 = lastRun.lambda1,
            lambda2 = lastRun.lambda2,
            visualVectorMap = visualVectorMap,
            lastRunResult = lastRun
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
}
