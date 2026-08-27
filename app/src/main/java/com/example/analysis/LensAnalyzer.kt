package com.example.analysis

import android.graphics.Bitmap
import android.graphics.Color
import com.example.model.LensMeasurementResult
import com.example.model.DisplacementVector
import kotlin.math.*

object LensAnalyzer {
    
    class Point(val x: Double, val y: Double)
    
    fun analyze(noLensFrames: List<Bitmap>, withLensFrames: List<Bitmap>): LensMeasurementResult {
        if (noLensFrames.isEmpty() || withLensFrames.isEmpty()) {
            return emptyResult("LOW - Missing Frames")
        }

        val width = noLensFrames[0].width
        val height = noLensFrames[0].height
        val cx = width / 2.0
        val cy = height / 2.0
        val lensRadius = min(width, height) * 0.35
        
        // 1. Multi-frame averaging / median of dots
        val refDots = extractStableDots(noLensFrames)
        val testDotsLocal = extractStableDots(withLensFrames)
        
        // Split dots
        val refInner = mutableListOf<Point>(); val refOuter = mutableListOf<Point>()
        for (p in refDots) {
            if (hypot(p.x - cx, p.y - cy) < lensRadius * 0.9) refInner.add(p)
            else if (hypot(p.x - cx, p.y - cy) > lensRadius * 1.1) refOuter.add(p)
        }
        
        val testInnerLocal = mutableListOf<Point>(); val testOuterLocal = mutableListOf<Point>()
        for (p in testDotsLocal) {
            if (hypot(p.x - cx, p.y - cy) < lensRadius * 0.9) testInnerLocal.add(p)
            else if (hypot(p.x - cx, p.y - cy) > lensRadius * 1.1) testOuterLocal.add(p)
        }
        
        // 2. Global Registration (using Outer dots)
        var globalAffine = doubleArrayOf(1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        var registrationRms = 0.0
        var inliersCount = 0
        
        if (refOuter.size >= 3 && testOuterLocal.size >= 3) {
            // Find translation first (RANSAC-ish)
            var bestTx = 0.0; var bestTy = 0.0; var maxInliers = -1
            for (i in 0 until min(50, testOuterLocal.size)) {
                for (j in 0 until min(50, refOuter.size)) {
                    val tx = refOuter[j].x - testOuterLocal[i].x
                    val ty = refOuter[j].y - testOuterLocal[i].y
                    var inliers = 0
                    for (tp in testOuterLocal) {
                        for (rp in refOuter) {
                            if (hypot(tp.x + tx - rp.x, tp.y + ty - rp.y) < 15.0) {
                                inliers++; break
                            }
                        }
                    }
                    if (inliers > maxInliers) {
                        maxInliers = inliers; bestTx = tx; bestTy = ty
                    }
                }
            }
            
            // Match with translation
            val matchedSrc = mutableListOf<Point>()
            val matchedDst = mutableListOf<Point>()
            for (tp in testOuterLocal) {
                var bestD = 15.0; var bestRp: Point? = null
                for (rp in refOuter) {
                    val d = hypot(tp.x + bestTx - rp.x, tp.y + bestTy - rp.y)
                    if (d < bestD) { bestD = d; bestRp = rp }
                }
                if (bestRp != null) {
                    matchedSrc.add(tp); matchedDst.add(bestRp)
                }
            }
            
            inliersCount = matchedSrc.size
            if (matchedSrc.size >= 3) {
                globalAffine = computeAffine(matchedSrc, matchedDst) ?: globalAffine
                // calculate RMS
                var sqErr = 0.0
                for (i in matchedSrc.indices) {
                    val wp = applyAffine(matchedSrc[i], globalAffine)
                    sqErr += hypot(wp.x - matchedDst[i].x, wp.y - matchedDst[i].y).pow(2)
                }
                registrationRms = sqrt(sqErr / matchedSrc.size)
            }
        }
        
        // Warp all test inner dots
        val testInner = testInnerLocal.map { applyAffine(it, globalAffine) }
        
        // 3. Match Inner Dots
        val validMatches = mutableListOf<Pair<Point, Point>>()
        for (tp in testInner) {
            var bestD = 30.0; var bestRp: Point? = null
            for (rp in refInner) {
                val d = hypot(tp.x - rp.x, tp.y - rp.y)
                if (d < bestD) { bestD = d; bestRp = rp }
            }
            if (bestRp != null) {
                validMatches.add(Pair(bestRp, tp))
            }
        }
        
        val trackedCount = validMatches.size
        val vectors = mutableListOf<DisplacementVector>()
        var meanDx = 0.0; var meanDy = 0.0
        
        val pointsX = mutableListOf<Point>()
        val disps = mutableListOf<Point>()
        
        for (m in validMatches) {
            val r = m.first; val t = m.second
            vectors.add(DisplacementVector(r.x, r.y, t.x, t.y))
            meanDx += (t.x - r.x); meanDy += (t.y - r.y)
            pointsX.add(Point(r.x - cx, r.y - cy))
            disps.add(Point(t.x - r.x, t.y - r.y))
        }
        if (trackedCount > 0) { meanDx /= trackedCount; meanDy /= trackedCount }
        
        var L1 = 0.0; var L2 = 0.0; var theta1 = 0.0; var theta2 = 0.0
        var optCx = cx; var optCy = cy
        
        if (trackedCount >= 10) {
            val fieldAffine = computeAffine(pointsX, disps)
            if (fieldAffine != null) {
                val A = fieldAffine[0]; val B = fieldAffine[1]; val C = fieldAffine[2]
                val D = fieldAffine[3]; val E = fieldAffine[4]; val F = fieldAffine[5]
                
                // Optical Center
                val detA = A * E - B * D
                if (abs(detA) > 1e-8) {
                    val X_oc = (B * F - C * E) / detA
                    val Y_oc = (C * D - A * F) / detA
                    optCx = cx + X_oc
                    optCy = cy + Y_oc
                }
                
                // Eigen values of symmetric part
                val Sxy = (B + D) / 2.0
                val tr = A + E
                val detS = A * E - Sxy * Sxy
                val root = sqrt(max(0.0, tr * tr / 4.0 - detS))
                L1 = tr / 2.0 + root
                L2 = tr / 2.0 - root
                
                theta1 = atan2(L1 - A, Sxy) * 180.0 / PI
                if (theta1 < 0) theta1 += 180.0
                theta2 = theta1 + 90.0
            }
        }
        
        val confidence = if (trackedCount >= 50) "HIGH" else if (trackedCount >= 30) "MEDIUM" else "LOW"
        val coverage = (trackedCount.toDouble() / max(1.0, refInner.size.toDouble()) * 100).toInt()
        
        return LensMeasurementResult(
            sph = 0.0, cyl = 0.0, axis = 0.0, calibrated = false,
            confidence = confidence,
            trackedPoints = trackedCount,
            coverage = coverage,
            meanDx = meanDx, meanDy = meanDy,
            p1 = L1, p1Angle = theta1,
            p2 = L2, p2Angle = theta2,
            registrationRms = registrationRms,
            ransacInliers = inliersCount,
            imageWidth = width, imageHeight = height,
            geometricCenterX = cx, geometricCenterY = cy,
            opticalCenterX = optCx, opticalCenterY = optCy,
            lensRadius = lensRadius,
            vectors = vectors
        )
    }

    private fun extractStableDots(frames: List<Bitmap>): List<Point> {
        val allDots = mutableListOf<List<Point>>()
        for (frame in frames) {
            allDots.add(detectBlobs(frame))
        }
        
        val dotClusters = mutableListOf<MutableList<Point>>()
        for (frameDots in allDots) {
            for (dot in frameDots) {
                var found = false
                for (cluster in dotClusters) {
                    val center = cluster[0]
                    if (hypot(center.x - dot.x, center.y - dot.y) < 15.0) {
                        cluster.add(dot)
                        found = true
                        break
                    }
                }
                if (!found) {
                    dotClusters.add(mutableListOf(dot))
                }
            }
        }
        
        val stableDots = mutableListOf<Point>()
        val minSupport = frames.size / 2
        for (cluster in dotClusters) {
            if (cluster.size >= minSupport) {
                val xs = cluster.map { it.x }.sorted()
                val ys = cluster.map { it.y }.sorted()
                stableDots.add(Point(xs[xs.size / 2], ys[ys.size / 2]))
            }
        }
        return stableDots
    }

    private fun detectBlobs(bitmap: Bitmap): List<Point> {
        val w = bitmap.width
        val h = bitmap.height
        val pixels = IntArray(w * h)
        bitmap.getPixels(pixels, 0, w, 0, 0, w, h)
        
        var sumLum = 0.0
        for (p in pixels) {
            sumLum += (Color.red(p) + Color.green(p) + Color.blue(p)) / 3.0
        }
        val meanLum = sumLum / pixels.size
        val threshold = (meanLum - 40).toInt().coerceIn(20, 230)
        
        val visited = BooleanArray(w * h)
        val blobs = mutableListOf<Point>()
        val q = IntArray(w * h)
        
        for (y in 2 until h-2 step 2) {
            for (x in 2 until w-2 step 2) {
                val idx = y * w + x
                if (visited[idx]) continue
                
                val p = pixels[idx]
                val lum = (Color.red(p) + Color.green(p) + Color.blue(p)) / 3
                if (lum < threshold) {
                    var sumX = 0.0; var sumY = 0.0; var count = 0
                    var minX = x; var maxX = x
                    var minY = y; var maxY = y
                    
                    var head = 0; var tail = 0
                    q[tail++] = idx
                    visited[idx] = true
                    
                    while (head < tail) {
                        val curr = q[head++]
                        val cx = curr % w
                        val cy = curr / w
                        
                        sumX += cx; sumY += cy; count++
                        if (cx < minX) minX = cx
                        if (cx > maxX) maxX = cx
                        if (cy < minY) minY = cy
                        if (cy > maxY) maxY = cy
                        
                        if (count > 800) break
                        
                        for (dy in -1..1) {
                            for (dx in -1..1) {
                                if (dx == 0 && dy == 0) continue
                                val nx = cx + dx
                                val ny = cy + dy
                                if (nx in 0 until w && ny in 0 until h) {
                                    val nidx = ny * w + nx
                                    if (!visited[nidx]) {
                                        val np = pixels[nidx]
                                        val nlum = (Color.red(np) + Color.green(np) + Color.blue(np)) / 3
                                        if (nlum < threshold) {
                                            visited[nidx] = true
                                            q[tail++] = nidx
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    if (count in 10..800) {
                        val bw = maxX - minX
                        val bh = maxY - minY
                        if (bw > 2 && bh > 2) {
                            val aspect = bw.toDouble() / bh.toDouble()
                            if (aspect in 0.3..3.3) {
                                blobs.add(Point(sumX / count, sumY / count))
                            }
                        }
                    }
                }
            }
        }
        return blobs
    }

    private fun computeAffine(src: List<Point>, dst: List<Point>): DoubleArray? {
        if (src.size < 3) return null
        var sx = 0.0; var sy = 0.0; var sxx = 0.0; var syy = 0.0; var sxy = 0.0
        var su = 0.0; var sux = 0.0; var suy = 0.0
        var sv = 0.0; var svx = 0.0; var svy = 0.0
        val n = src.size.toDouble()
        
        for (i in src.indices) {
            val x = src[i].x; val y = src[i].y
            val u = dst[i].x; val v = dst[i].y
            
            sx += x; sy += y
            sxx += x*x; syy += y*y; sxy += x*y
            su += u; sux += u*x; suy += u*y
            sv += v; svx += v*x; svy += v*y
        }
        
        val det = sxx*(syy*n - sy*sy) - sxy*(sxy*n - sx*sy) + sx*(sxy*sy - sx*syy)
        if (abs(det) < 1e-10) return null
        
        val inv00 = (syy*n - sy*sy) / det
        val inv01 = (sx*sy - sxy*n) / det
        val inv02 = (sxy*sy - sx*syy) / det
        val inv11 = (sxx*n - sx*sx) / det
        val inv12 = (sx*sxy - sxx*sy) / det
        val inv22 = (sxx*syy - sxy*sxy) / det
        
        val a = inv00*sux + inv01*suy + inv02*su
        val b = inv01*sux + inv11*suy + inv12*su
        val c = inv02*sux + inv12*suy + inv22*su
        
        val d = inv00*svx + inv01*svy + inv02*sv
        val e = inv01*svx + inv11*svy + inv12*sv
        val f = inv02*svx + inv12*svy + inv22*sv
        
        return doubleArrayOf(a, b, c, d, e, f)
    }

    private fun applyAffine(p: Point, affine: DoubleArray): Point {
        return Point(
            affine[0]*p.x + affine[1]*p.y + affine[2],
            affine[3]*p.x + affine[4]*p.y + affine[5]
        )
    }
    
    private fun emptyResult(confidence: String): LensMeasurementResult {
        return LensMeasurementResult(0.0, 0.0, 0.0, false, confidence, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, emptyList())
    }
}
