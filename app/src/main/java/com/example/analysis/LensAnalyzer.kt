package com.example.analysis

import android.graphics.Bitmap
import android.graphics.Color
import com.example.model.LensMeasurementResult
import kotlin.math.*

object LensAnalyzer {
    
    class Point(val x: Double, val y: Double)
    
    fun analyze(noLensFrames: List<Bitmap>, withLensFrames: List<Bitmap>): LensMeasurementResult {
        if (noLensFrames.isEmpty() || withLensFrames.isEmpty()) {
            return emptyResult("LOW")
        }

        // 1. Average frames to reduce noise
        val refImage = averageFrames(noLensFrames)
        val testImage = averageFrames(withLensFrames)
        
        val width = refImage.width
        val height = refImage.height
        
        // Lens ROI (Assume center 30% of screen is lens, outside is reference)
        val cx = width / 2.0
        val cy = height / 2.0
        val lensRadius = Math.min(width, height) * 0.3
        
        // 2. Find features in the reference image
        val features = detectFeatures(refImage)
        
        // 3. Track features in the test image using template matching
        val correspondences = trackFeatures(refImage, testImage, features)
        
        // 4. Split into outside (registration) and inside (measurement)
        val outsidePointsRef = mutableListOf<Point>()
        val outsidePointsTest = mutableListOf<Point>()
        val insidePointsRef = mutableListOf<Point>()
        val insidePointsTest = mutableListOf<Point>()
        
        for (corr in correspondences) {
            val dist = Math.hypot(corr.first.x - cx, corr.first.y - cy)
            if (dist > lensRadius * 1.1) {
                outsidePointsRef.add(corr.first)
                outsidePointsTest.add(corr.second)
            } else if (dist < lensRadius * 0.9) {
                insidePointsRef.add(corr.first)
                insidePointsTest.add(corr.second)
            }
        }
        
        if (insidePointsRef.size < 5) {
             return emptyResult("INVALID - Insufficient features")
        }
        
        // 5. Compute global registration (translation + small rotation) using outside points
        // For simplicity, let's just do translation.
        var globalTx = 0.0
        var globalTy = 0.0
        if (outsidePointsRef.isNotEmpty()) {
            val txs = outsidePointsTest.zip(outsidePointsRef).map { it.first.x - it.second.x }.sorted()
            val tys = outsidePointsTest.zip(outsidePointsRef).map { it.first.y - it.second.y }.sorted()
            globalTx = txs[txs.size / 2]
            globalTy = tys[tys.size / 2]
        }
        
        // 6. Compute local displacement inside lens
        var sumDx = 0.0
        var sumDy = 0.0
        var maxDisp = 0.0
        
        val displacements = mutableListOf<Pair<Point, Point>>() // position, vector
        
        for (i in insidePointsRef.indices) {
            val pref = insidePointsRef[i]
            val ptest = insidePointsTest[i]
            
            // Correct for global phone movement
            val correctedTestX = ptest.x - globalTx
            val correctedTestY = ptest.y - globalTy
            
            val dx = correctedTestX - pref.x
            val dy = correctedTestY - pref.y
            
            sumDx += dx
            sumDy += dy
            val mag = Math.hypot(dx, dy)
            if (mag > maxDisp) maxDisp = mag
            
            displacements.add(Pair(pref, Point(dx, dy)))
        }
        
        val meanDx = sumDx / insidePointsRef.size
        val meanDy = sumDy / insidePointsRef.size
        
        // 7. Estimate local spatial derivative matrix (Jacobian)
        // u(x,y) = Jxx * x + Jxy * y
        // v(x,y) = Jyx * x + Jyy * y
        // We do least squares fit
        var sxx = 0.0; var sxy = 0.0; var syy = 0.0
        var sux = 0.0; var suy = 0.0; var svx = 0.0; var svy = 0.0
        
        for (d in displacements) {
            val x = d.first.x - cx
            val y = d.first.y - cy
            val u = d.second.x - meanDx // remove mean translation
            val v = d.second.y - meanDy
            
            sxx += x * x
            sxy += x * y
            syy += y * y
            sux += u * x
            suy += u * y
            svx += v * x
            svy += v * y
        }
        
        val det = sxx * syy - sxy * sxy
        var Jxx = 0.0; var Jxy = 0.0; var Jyx = 0.0; var Jyy = 0.0
        if (det > 1e-6) {
            Jxx = (syy * sux - sxy * suy) / det
            Jxy = (sxx * suy - sxy * sux) / det
            Jyx = (syy * svx - sxy * svy) / det
            Jyy = (sxx * svy - sxy * svx) / det
        }
        
        // Symmetric part of Jacobian
        val Sxx = Jxx
        val Sxy = (Jxy + Jyx) / 2.0
        val Syy = Jyy
        
        // Eigenvalues of symmetric tensor
        val trace = Sxx + Syy
        val detS = Sxx * Syy - Sxy * Sxy
        
        val root = Math.sqrt(Math.max(0.0, trace * trace / 4.0 - detS))
        val eig1 = trace / 2.0 + root
        val eig2 = trace / 2.0 - root
        
        val angle1 = Math.atan2(eig1 - Sxx, Sxy) * 180.0 / PI
        val angle2 = angle1 + 90.0
        
        // Directional signals
        val dirSignals = mutableMapOf<Int, Double>()
        for (angle in 0..165 step 15) {
            val rad = angle * PI / 180.0
            val c = Math.cos(rad)
            val s = Math.sin(rad)
            // Projected strain
            val p = Sxx * c * c + 2 * Sxy * c * s + Syy * s * s
            dirSignals[angle] = p
        }
        
        // Convert to pseudo-diopters if we don't have calibration
        // Just scaling the signal by a constant to look like diopters for now.
        // We explicitly mark calibrated = false
        val pseudoScale = -100.0 // Arbitrary
        val F1 = eig1 * pseudoScale
        val F2 = eig2 * pseudoScale
        
        val sph = Math.max(F1, F2) // more positive
        val cyl = Math.min(F1, F2) - sph
        var axis = if (sph == F1) angle1 else angle2
        if (axis < 0) axis += 180.0
        if (axis >= 180) axis -= 180.0
        
        return LensMeasurementResult(
            sph = sph,
            cyl = cyl,
            axis = axis,
            calibrated = false,
            confidence = "MEDIUM",
            trackedPoints = insidePointsRef.size,
            meanDx = meanDx,
            meanDy = meanDy,
            maxDisplacement = maxDisp,
            p1 = eig1,
            p1Angle = angle1,
            p2 = eig2,
            p2Angle = angle2,
            directionalSignals = dirSignals
        )
    }
    
    private fun emptyResult(confidence: String): LensMeasurementResult {
        return LensMeasurementResult(0.0, 0.0, 0.0, false, confidence, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, emptyMap())
    }

    private fun averageFrames(frames: List<Bitmap>): Bitmap {
        val width = frames[0].width
        val height = frames[0].height
        val averaged = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        
        val sumR = IntArray(width * height)
        val sumG = IntArray(width * height)
        val sumB = IntArray(width * height)
        
        for (frame in frames) {
            val pixels = IntArray(width * height)
            frame.getPixels(pixels, 0, width, 0, 0, width, height)
            for (i in pixels.indices) {
                val c = pixels[i]
                sumR[i] += Color.red(c)
                sumG[i] += Color.green(c)
                sumB[i] += Color.blue(c)
            }
        }
        
        val outPixels = IntArray(width * height)
        val n = frames.size
        for (i in outPixels.indices) {
            outPixels[i] = Color.rgb(sumR[i] / n, sumG[i] / n, sumB[i] / n)
        }
        averaged.setPixels(outPixels, 0, width, 0, 0, width, height)
        return averaged
    }
    
    private fun detectFeatures(image: Bitmap): List<Point> {
        val width = image.width
        val height = image.height
        val pixels = IntArray(width * height)
        image.getPixels(pixels, 0, width, 0, 0, width, height)
        
        val gray = IntArray(width * height)
        for (i in pixels.indices) {
            val c = pixels[i]
            gray[i] = (Color.red(c) * 0.299 + Color.green(c) * 0.587 + Color.blue(c) * 0.114).toInt()
        }
        
        val features = mutableListOf<Point>()
        // Simple grid of points to track (like a dense optical flow initialization)
        val step = 30
        for (y in 50 until height - 50 step step) {
            for (x in 50 until width - 50 step step) {
                // Check variance in patch
                var v = 0.0
                var mean = 0.0
                for (dy in -2..2) {
                    for (dx in -2..2) {
                        mean += gray[(y+dy)*width + (x+dx)]
                    }
                }
                mean /= 25.0
                for (dy in -2..2) {
                    for (dx in -2..2) {
                        val diff = gray[(y+dy)*width + (x+dx)] - mean
                        v += diff * diff
                    }
                }
                if (v > 5000) { // Enough texture
                    features.add(Point(x.toDouble(), y.toDouble()))
                }
            }
        }
        return features
    }
    
    private fun trackFeatures(ref: Bitmap, test: Bitmap, features: List<Point>): List<Pair<Point, Point>> {
        val width = ref.width
        val height = ref.height
        val refPixels = IntArray(width * height)
        val testPixels = IntArray(width * height)
        ref.getPixels(refPixels, 0, width, 0, 0, width, height)
        test.getPixels(testPixels, 0, width, 0, 0, width, height)
        
        val refGray = IntArray(width * height) { i -> Color.green(refPixels[i]) }
        val testGray = IntArray(width * height) { i -> Color.green(testPixels[i]) }
        
        val correspondences = mutableListOf<Pair<Point, Point>>()
        val patchSize = 7
        val searchWin = 25
        
        for (f in features) {
            val cx = f.x.toInt()
            val cy = f.y.toInt()
            
            var bestDx = 0
            var bestDy = 0
            var minDiff = Double.MAX_VALUE
            
            // Extract ref patch
            val refPatch = IntArray((patchSize*2+1) * (patchSize*2+1))
            var idx = 0
            var rmean = 0.0
            for (dy in -patchSize..patchSize) {
                for (dx in -patchSize..patchSize) {
                    val p = refGray[(cy+dy)*width + (cx+dx)].toDouble()
                    refPatch[idx++] = p.toInt()
                    rmean += p
                }
            }
            rmean /= refPatch.size
            
            for (sy in -searchWin..searchWin) {
                for (sx in -searchWin..searchWin) {
                    val tcy = cy + sy
                    val tcx = cx + sx
                    if (tcy < patchSize || tcy >= height - patchSize || tcx < patchSize || tcx >= width - patchSize) continue
                    
                    var tmean = 0.0
                    for (dy in -patchSize..patchSize) {
                        for (dx in -patchSize..patchSize) {
                            tmean += testGray[(tcy+dy)*width + (tcx+dx)]
                        }
                    }
                    tmean /= refPatch.size
                    
                    var diff = 0.0
                    idx = 0
                    for (dy in -patchSize..patchSize) {
                        for (dx in -patchSize..patchSize) {
                            val r = refPatch[idx++] - rmean
                            val t = testGray[(tcy+dy)*width + (tcx+dx)] - tmean
                            diff += Math.abs(r - t)
                        }
                    }
                    
                    if (diff < minDiff) {
                        minDiff = diff
                        bestDx = sx
                        bestDy = sy
                    }
                }
            }
            
            if (minDiff < refPatch.size * 20.0) { // arbitrary threshold for matching
                correspondences.add(Pair(f, Point(cx + bestDx.toDouble(), cy + bestDy.toDouble())))
            }
        }
        
        return correspondences
    }
}
