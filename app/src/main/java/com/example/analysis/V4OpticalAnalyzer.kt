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

data class V4RunResult(
    val success: Boolean,
    val errorMessage: String = "",
    val axis: Double = 0.0,
    val lambda1: Double = 0.0,
    val lambda2: Double = 0.0,
    val isotropic: Double = 0.0,
    val anisotropic: Double = 0.0,
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
    val refHeight: Int = 0,
    val globalScaleAmbiguous: Boolean = false,
    val framesCaptured: Int = 0,
    val framesAccepted: Int = 0,
    val framesRejected: Int = 0,
    val candidateMatches: Int = 0,
    val acceptedMatches: Int = 0,
    val rejectedMatches: Int = 0,
    val matrixRank: Int = 0,
    val conditionNumber: Double = 0.0,
    val degeneracyStatus: String = "OK",
    val matchRejections: Map<String, Int> = emptyMap(),
    val spatialCoveragePct: Double = 0.0,
    val quadrantCoverage: Int = 0,
    val temporalTrackCount: Int = 0,
    val stableTrackCount: Int = 0,
    val medianTrackLifetime: Double = 0.0,
    val rejectedReferencePoints: List<Point> = emptyList(),
    val unmatchedLensPoints: List<Point> = emptyList()
)

data class V4Result(
    val success: Boolean,
    val errorMessage: String = "",
    val sphDisplay: String = "",
    val cylDisplay: String = "",
    val axisDisplay: String = "",
    val lambda1: Double = 0.0,
    val lambda2: Double = 0.0,
    val isotropic: Double = 0.0,
    val anisotropic: Double = 0.0,
    val lambda1Std: Double = 0.0,
    val lambda2Std: Double = 0.0,
    val isotropicStd: Double = 0.0,
    val anisotropicStd: Double = 0.0,
    val allRuns: List<V4RunResult> = emptyList(),
    val trackedDots: Int = 0,
    val registrationRms: Double = 0.0,
    val ransacInliers: Int = 0,
    val fieldFitRms: Double = 0.0,
    val refDotCount: Int = 0,
    val lensDotCount: Int = 0,
    val meanDx: Double = 0.0,
    val meanDy: Double = 0.0,
    val visualVectorMap: Bitmap? = null,
    val lastRunResult: V4RunResult? = null,
    val globalScaleAmbiguous: Boolean = false
)

private data class AggResult(
    val success: Boolean,
    val errorMessage: String,
    val points: List<Point>,
    val frames: Int,
    val accepted: Int,
    val rejected: Int,
    val stableTrackCount: Int = 0,
    val medianTrackLifetime: Double = 0.0,
    val rejectedReferencePoints: List<Point> = emptyList(),
    val unmatchedLensPoints: List<Point> = emptyList()
)

object V4OpticalAnalyzer {

    private fun detectDots(bitmap: Bitmap): List<Point> {
        val mat = Mat()
        Utils.bitmapToMat(bitmap, mat)
        val gray = Mat()
        Imgproc.cvtColor(mat, gray, Imgproc.COLOR_BGR2GRAY)
        
        val thresh = Mat()
        Imgproc.adaptiveThreshold(gray, thresh, 255.0, Imgproc.ADAPTIVE_THRESH_GAUSSIAN_C, Imgproc.THRESH_BINARY_INV, 11, 2.0)
        
        val contours = mutableListOf<MatOfPoint>()
        val hierarchy = Mat()
        Imgproc.findContours(thresh, contours, hierarchy, Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_SIMPLE)
        
        val points = mutableListOf<Point>()
        for (contour in contours) {
            val area = Imgproc.contourArea(contour)
            if (area > 10.0 && area < 500.0) {
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

    private fun aggregateFrames(frames: List<Bitmap>): AggResult {
        if (frames.isEmpty()) return AggResult(false, "No frames", emptyList(), 0, 0, 0)
        
        val allKeypoints = frames.map { detectDots(it) }
        val baseIdx = allKeypoints.indices.maxByOrNull { allKeypoints[it].size } ?: 0
        val basePoints = allKeypoints[baseIdx]
        
        if (basePoints.size < 10) return AggResult(false, "Not enough points in base frame", emptyList(), frames.size, 0, frames.size)
        
        val pointGroups = Array(basePoints.size) { mutableListOf<Point>() }
        
        var accepted = 0
        var rejected = 0
        
        for (i in frames.indices) {
            val pts = allKeypoints[i]
            if (pts.size < 10) {
                rejected++
                continue
            }
            
            val srcMat = MatOfPoint2f()
            val dstMat = MatOfPoint2f()
            
            val matchedBase = mutableListOf<Point>()
            val matchedCurr = mutableListOf<Point>()
            
            for (pt1 in basePoints) {
                var bestDist = Double.MAX_VALUE
                var bestPt2: Point? = null
                for (pt2 in pts) {
                    val dist = hypot(pt1.x - pt2.x, pt1.y - pt2.y)
                    if (dist < bestDist && dist < 100.0) {
                        bestDist = dist
                        bestPt2 = pt2
                    }
                }
                if (bestPt2 != null) {
                    matchedBase.add(pt1)
                    matchedCurr.add(bestPt2)
                }
            }
            
            if (matchedBase.size < 10) {
                rejected++
                continue
            }
            
            srcMat.fromList(matchedCurr)
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
        val trackLifetimes = mutableListOf<Double>()
        var stableCount = 0
        
        for (group in pointGroups) {
            val lifetime = group.size.toDouble() / max(1, frames.size)
            if (group.size > 0) {
                trackLifetimes.add(lifetime)
            }
            
            if (group.size > frames.size * 0.3) {
                stableCount++
                group.sortBy { it.x }
                val medianX = group[group.size / 2].x
                group.sortBy { it.y }
                val medianY = group[group.size / 2].y
                
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
        
        trackLifetimes.sort()
        val medianLifetime = if (trackLifetimes.isNotEmpty()) trackLifetimes[trackLifetimes.size / 2] else 0.0
        
        return AggResult(true, "", finalPoints, frames.size, accepted, rejected, stableCount, medianLifetime)
    }
    
    private fun estimateSpacing(pts: List<Point>): Double {
        if (pts.size < 2) return 50.0
        val dists = mutableListOf<Double>()
        for (p1 in pts) {
            var minDist = Double.MAX_VALUE
            for (p2 in pts) {
                if (p1 === p2) continue
                val d = hypot(p1.x - p2.x, p1.y - p2.y)
                if (d < minDist) minDist = d
            }
            if (minDist != Double.MAX_VALUE) {
                dists.add(minDist)
            }
        }
        if (dists.isEmpty()) return 50.0
        dists.sort()
        return dists[dists.size / 2]
    }

    private fun assignGridTopology(points: List<Point>, spacing: Double): Map<Pair<Int, Int>, Point> {
        if (points.isEmpty()) return emptyMap()
        
        val angles = mutableListOf<Double>()
        for (i in points.indices) {
            for (j in i + 1 until points.size) {
                val p1 = points[i]
                val p2 = points[j]
                val dx = p2.x - p1.x
                val dy = p2.y - p1.y
                val dist = hypot(dx, dy)
                if (dist > spacing * 0.5 && dist < spacing * 1.5) {
                    var a = atan2(dy, dx)
                    while (a < 0) a += PI / 2.0
                    while (a >= PI / 2.0) a -= PI / 2.0
                    angles.add(a)
                }
            }
        }
        
        val medianAngle = if (angles.isNotEmpty()) {
            angles.sort()
            angles[angles.size / 2]
        } else 0.0
        
        val cosA = cos(-medianAngle)
        val sinA = sin(-medianAngle)
        
        val cx = points.map { it.x }.average()
        val cy = points.map { it.y }.average()
        
        val grid = mutableMapOf<Pair<Int, Int>, Point>()
        for (p in points) {
            val tx = p.x - cx
            val ty = p.y - cy
            val rx = tx * cosA - ty * sinA
            val ry = tx * sinA + ty * cosA
            
            val col = (rx / spacing).roundToInt()
            val row = (ry / spacing).roundToInt()
            
            var finalR = row
            var finalC = col
            while (grid.containsKey(Pair(finalR, finalC))) {
                finalC++
            }
            grid[Pair(finalR, finalC)] = p
        }
        return grid
    }

    suspend fun analyze(noLensFrames: List<Bitmap>, withLensFrames: List<Bitmap>): V4RunResult = withContext(Dispatchers.Default) {
        if (noLensFrames.isEmpty() || withLensFrames.isEmpty()) {
            return@withContext V4RunResult(success = false, errorMessage = "Missing frames")
        }
        
        try {
            val refAgg = aggregateFrames(noLensFrames)
            if (!refAgg.success) {
                return@withContext V4RunResult(success = false, errorMessage = "Ref aggregation failed: ${refAgg.errorMessage}")
            }
            val baseRefPoints = refAgg.points
            
            val lensAgg = aggregateFrames(withLensFrames)
            if (!lensAgg.success) {
                return@withContext V4RunResult(success = false, errorMessage = "Lens aggregation failed: ${lensAgg.errorMessage}")
            }
            val baseLensPoints = lensAgg.points
            
            val spacing = estimateSpacing(baseRefPoints)
            
            val rejections = mutableMapOf(
                "geometric_gate" to 0,
                "distance_gate" to 0,
                "ransac_rejection" to 0,
                "roi_rejection" to 0,
                "duplicate_match" to 0,
                "registration_inconsistency" to 0,
                "low_confidence" to 0,
                "other" to 0
            )
            
            val w = noLensFrames[0].width.toDouble()
            val h = noLensFrames[0].height.toDouble()
            
            val gridMap = assignGridTopology(baseRefPoints, spacing)

            val binSize = spacing * 0.2
            val histogram = HashMap<Pair<Int, Int>, Int>()
            for (ptRef in baseRefPoints) {
                for (ptLens in baseLensPoints) {
                    val dx = ptLens.x - ptRef.x
                    val dy = ptLens.y - ptRef.y
                    if (hypot(dx, dy) < spacing * 4.0) {
                        val binX = (dx / binSize).roundToInt()
                        val binY = (dy / binSize).roundToInt()
                        val key = Pair(binX, binY)
                        histogram[key] = histogram.getOrDefault(key, 0) + 1
                    }
                }
            }
            
            var bestBin = Pair(0, 0)
            var maxCount = 0
            for ((bin, count) in histogram) {
                if (count > maxCount) {
                    maxCount = count
                    bestBin = bin
                }
            }
            
            val globalTx = bestBin.first * binSize
            val globalTy = bestBin.second * binSize
            
            val acceptedMatches = mutableMapOf<Pair<Int, Int>, Point>()
            
            for ((coord, ptRef) in gridMap) {
                val shiftedX = ptRef.x + globalTx
                val shiftedY = ptRef.y + globalTy
                
                var bestDist = Double.MAX_VALUE
                var bestLens: Point? = null
                for (ptLens in baseLensPoints) {
                    val dist = hypot(ptLens.x - shiftedX, ptLens.y - shiftedY)
                    if (dist < bestDist) {
                        bestDist = dist
                        bestLens = ptLens
                    }
                }
                
                if (bestLens != null && bestDist < spacing * 0.4) {
                    if (!acceptedMatches.containsValue(bestLens)) {
                        acceptedMatches[coord] = bestLens
                    }
                }
            }

            var changed = true
            while (changed) {
                changed = false
                
                for ((coord, ptRef) in gridMap) {
                    if (acceptedMatches.containsKey(coord)) continue
                    
                    val (r, c) = coord
                    val neighbors = listOf(Pair(r-1, c), Pair(r+1, c), Pair(r, c-1), Pair(r, c+1),
                                           Pair(r-1, c-1), Pair(r-1, c+1), Pair(r+1, c-1), Pair(r+1, c+1))
                    val matchedNeighbors = neighbors.filter { acceptedMatches.containsKey(it) }
                    
                    if (matchedNeighbors.isNotEmpty()) {
                        var sumDx = 0.0
                        var sumDy = 0.0
                        for (nCoord in matchedNeighbors) {
                            val nRef = gridMap[nCoord]!!
                            val nLens = acceptedMatches[nCoord]!!
                            sumDx += (nLens.x - nRef.x)
                            sumDy += (nLens.y - nRef.y)
                        }
                        val avgDx = sumDx / matchedNeighbors.size
                        val avgDy = sumDy / matchedNeighbors.size
                        
                        val predX = ptRef.x + avgDx
                        val predY = ptRef.y + avgDy
                        
                        var bestDist = Double.MAX_VALUE
                        var bestLens: Point? = null
                        for (ptLens in baseLensPoints) {
                            if (acceptedMatches.containsValue(ptLens)) continue
                            val dist = hypot(ptLens.x - predX, ptLens.y - predY)
                            if (dist < bestDist) {
                                bestDist = dist
                                bestLens = ptLens
                            }
                        }
                        
                        if (bestLens != null && bestDist < spacing * 0.7) {
                            acceptedMatches[coord] = bestLens
                            changed = true
                        }
                    }
                }
            }
            
            if (acceptedMatches.size >= 10) {
                val srcList = acceptedMatches.values.map { gridMap[acceptedMatches.entries.find { e -> e.value == it }!!.key]!! }
                val dstList = acceptedMatches.values.toList()
                val srcMat = MatOfPoint2f().apply { fromList(srcList) }
                val dstMat = MatOfPoint2f().apply { fromList(dstList) }
                val inliers = Mat()
                val affine = Calib3d.estimateAffine2D(srcMat, dstMat, inliers, Calib3d.RANSAC, spacing * 0.5)
                
                if (!affine.empty()) {
                    for ((coord, ptRef) in gridMap) {
                        if (acceptedMatches.containsKey(coord)) continue
                        
                        val ptMat = MatOfPoint2f(ptRef)
                        val predMat = MatOfPoint2f()
                        Core.transform(ptMat, predMat, affine)
                        val predX = predMat.toArray()[0].x
                        val predY = predMat.toArray()[0].y
                        
                        var bestDist = Double.MAX_VALUE
                        var bestLens: Point? = null
                        for (ptLens in baseLensPoints) {
                            if (acceptedMatches.containsValue(ptLens)) continue
                            val dist = hypot(ptLens.x - predX, ptLens.y - predY)
                            if (dist < bestDist) {
                                bestDist = dist
                                bestLens = ptLens
                            }
                        }
                        
                        if (bestLens != null && bestDist < spacing * 0.7) {
                            acceptedMatches[coord] = bestLens
                        }
                    }
                }
            }
            
            val candidateRef = mutableListOf<Point>()
            val candidateLens = mutableListOf<Point>()
            
            val rejectedRefs = mutableListOf<Point>()
            for ((coord, ptRef) in gridMap) {
                if (acceptedMatches.containsKey(coord)) {
                    candidateRef.add(ptRef)
                    candidateLens.add(acceptedMatches[coord]!!)
                } else {
                    rejectedRefs.add(ptRef)
                    rejections["topology_rejection"] = rejections.getOrDefault("topology_rejection", 0) + 1
                }
            }
            
            val unmatchedLens = baseLensPoints.filter { !acceptedMatches.containsValue(it) }
            rejections["unmatched_lens_dots"] = unmatchedLens.size
            
            val cx = w / 2.0
            val cy = h / 2.0
            var q1 = 0; var q2 = 0; var q3 = 0; var q4 = 0
            for (pt in candidateRef) {
                if (pt.x < cx && pt.y < cy) q1++
                if (pt.x >= cx && pt.y < cy) q2++
                if (pt.x < cx && pt.y >= cy) q3++
                if (pt.x >= cx && pt.y >= cy) q4++
            }
            rejections["Quad1_Matches"] = q1
            rejections["Quad2_Matches"] = q2
            rejections["Quad3_Matches"] = q3
            rejections["Quad4_Matches"] = q4
            
            val res = analyzePoints(candidateRef, candidateLens, w, h, baseRefPoints.size, baseLensPoints.size, spacing, rejections)
            
            return@withContext res.copy(
                framesCaptured = withLensFrames.size,
                framesAccepted = lensAgg.accepted,
                framesRejected = lensAgg.rejected,
                temporalTrackCount = lensAgg.points.size,
                stableTrackCount = lensAgg.stableTrackCount,
                medianTrackLifetime = lensAgg.medianTrackLifetime,
                rejectedReferencePoints = rejectedRefs,
                unmatchedLensPoints = unmatchedLens
            )
            
        } catch (e: Exception) {
            Log.e("V4OpticalAnalyzer", "Analyze failed", e)
            return@withContext V4RunResult(success = false, errorMessage = "Exception: ${e.message}")
        }
    }
    fun analyzePoints(matchedRef: List<Point>, matchedLens: List<Point>, w: Double, h: Double, baseRefDotCount: Int = 0, baseLensDotCount: Int = 0, spacing: Double = 30.0, rejections: MutableMap<String, Int> = mutableMapOf()): V4RunResult {
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
            
            val ptsToMeasureRef = mutableListOf<Point>()
            val ptsToMeasureLens = mutableListOf<Point>()
            
            if (useRigidFallback) {
                for (i in matchedRef.indices) {
                    if (maskArray[i].toInt() != 0) {
                        ptsToMeasureRef.add(matchedRef[i])
                        ptsToMeasureLens.add(matchedLens[i])
                    } else {
                        rejections["ransac_rejection"] = rejections.getOrDefault("ransac_rejection", 0) + 1
                    }
                }
            } else {
                for (i in anchorRef.indices) {
                    if (maskArray[i].toInt() == 0) {
                        rejections["ransac_rejection"] = rejections.getOrDefault("ransac_rejection", 0) + 1
                    }
                }
                ptsToMeasureRef.addAll(measurementRef)
                ptsToMeasureLens.addAll(measurementLens)
            }
            
            if (ptsToMeasureRef.size < 6) {
                 return V4RunResult(success = false, errorMessage = "Insufficient measurement points (<6)", candidateMatches = matchedRef.size, acceptedMatches = inliersCount, matchRejections = rejections)
            }
            
            var q1 = false; var q2 = false; var q3 = false; var q4 = false
            var minX = Double.MAX_VALUE; var maxX = -Double.MAX_VALUE
            var minY = Double.MAX_VALUE; var maxY = -Double.MAX_VALUE
            
            for (pt in ptsToMeasureRef) {
                if (pt.x < cx && pt.y < cy) q1 = true
                if (pt.x >= cx && pt.y < cy) q2 = true
                if (pt.x < cx && pt.y >= cy) q3 = true
                if (pt.x >= cx && pt.y >= cy) q4 = true
                
                if (pt.x < minX) minX = pt.x
                if (pt.x > maxX) maxX = pt.x
                if (pt.y < minY) minY = pt.y
                if (pt.y > maxY) maxY = pt.y
            }
            
            val quadCount = (if (q1) 1 else 0) + (if (q2) 1 else 0) + (if (q3) 1 else 0) + (if (q4) 1 else 0)
            val spreadX = maxX - minX
            val spreadY = maxY - minY
            val spatialCoveragePct = ((spreadX * spreadY) / (w * h)) * 100.0
            
            if (quadCount < 2 || spreadX < w * 0.1 || spreadY < h * 0.1) {
                rejections["roi_rejection"] = rejections.getOrDefault("roi_rejection", 0) + ptsToMeasureRef.size
                return V4RunResult(success = false, errorMessage = "Poor spatial coverage (quads: $quadCount, spread: ${spreadX.toInt()}x${spreadY.toInt()})", candidateMatches = matchedRef.size, acceptedMatches = ptsToMeasureRef.size, matchRejections = rejections, spatialCoveragePct = spatialCoveragePct, quadrantCoverage = quadCount)
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
                for (i in ptsToMeasureRef.indices) {
                    val dx = transformedLens[i].x - ptsToMeasureRef[i].x
                    val dy = transformedLens[i].y - ptsToMeasureRef[i].y
                    rSum += dx * dx + dy * dy
                }
                registrationRms = sqrt(rSum / max(1, ptsToMeasureRef.size))
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
                degeneracyStatus = "RANK_DEFICIENT"
            } else if (cond > 1e4 || cond.isNaN()) {
                degeneracyStatus = "ILL_CONDITIONED"
            }
            
            if (degeneracyStatus != "OK") {
                 return V4RunResult(success = false, errorMessage = "Degenerate geometric configuration: $degeneracyStatus",
                     candidateMatches = matchedRef.size, acceptedMatches = ptsToMeasureRef.size, matrixRank = rank, conditionNumber = cond, degeneracyStatus = degeneracyStatus, matchRejections = rejections)
            }
            
            val J_matrix = Mat()
            try {
                Core.solve(A, B, J_matrix, Core.DECOMP_SVD)
            } catch (e: Exception) {
                return V4RunResult(success = false, errorMessage = "OpenCV solve failed: ${e.message}",
                     candidateMatches = matchedRef.size, acceptedMatches = ptsToMeasureRef.size, matrixRank = rank, conditionNumber = cond, degeneracyStatus = "SOLVE_EXCEPTION", matchRejections = rejections)
            }
            
            val j00 = J_matrix.get(0, 0)[0]
            val j10 = J_matrix.get(0, 1)[0]
            val j01 = J_matrix.get(1, 0)[0]
            val j11 = J_matrix.get(1, 1)[0]
            
            if (j00.isNaN() || j10.isNaN() || j01.isNaN() || j11.isNaN() ||
                j00.isInfinite() || j10.isInfinite() || j01.isInfinite() || j11.isInfinite()) {
                return V4RunResult(success = false, errorMessage = "NaN/Infinity in optical field solution",
                     candidateMatches = matchedRef.size, acceptedMatches = ptsToMeasureRef.size, matrixRank = rank, conditionNumber = cond, degeneracyStatus = "NAN_INF", matchRejections = rejections)
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
            
            val maxAllowedRms = max(2.0, spacing * 0.15)
            if (fieldFitRms > maxAllowedRms) {
                rejections["low_confidence"] = rejections.getOrDefault("low_confidence", 0) + ptsToMeasureRef.size
                return V4RunResult(success = false, errorMessage = "Poor field fit (RMS $fieldFitRms > $maxAllowedRms)",
                     candidateMatches = matchedRef.size, acceptedMatches = ptsToMeasureRef.size, matrixRank = rank, conditionNumber = cond, degeneracyStatus = "POOR_FIT", matchRejections = rejections, fieldFitRms = fieldFitRms)
            }

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
                degeneracyStatus = degeneracyStatus,
                matchRejections = rejections,
                spatialCoveragePct = spatialCoveragePct,
                quadrantCoverage = quadCount
            )
        } catch (e: Exception) {
            Log.e("V4OpticalAnalyzer", "AnalyzePoints failed", e)
            return V4RunResult(success = false, errorMessage = "Exception: ${e.message}", degeneracyStatus = "EXCEPTION", matchRejections = rejections)
        }
    }
    suspend fun calculateRepeatability(results: List<V4RunResult>): V4Result = withContext(Dispatchers.Default) {
        if (results.size < 3) {
            return@withContext V4Result(success = false, errorMessage = "Need 3 runs")
        }
        
        if (results.any { !it.success }) {
            return@withContext V4Result(success = false, errorMessage = "One or more runs failed: " + results.first { !it.success }.errorMessage)
        }
        
        val l1_vals = results.map { it.lambda1 }.sorted()
        if (l1_vals.last() - l1_vals.first() > 0.15) {
            return@withContext V4Result(success = false, errorMessage = "REPEATABILITY FAILED (Lambda1 spread > 0.15)", allRuns = results, lastRunResult = results.last())
        }
        
        val lambda1Mean = results.map { it.lambda1 }.average()
        val lambda2Mean = results.map { it.lambda2 }.average()
        val isotropicMean = results.map { it.isotropic }.average()
        val anisotropicMean = results.map { it.anisotropic }.average()
        
        val lambda1Std = sqrt(results.map { (it.lambda1 - lambda1Mean) * (it.lambda1 - lambda1Mean) }.average())
        val lambda2Std = sqrt(results.map { (it.lambda2 - lambda2Mean) * (it.lambda2 - lambda2Mean) }.average())
        val isotropicStd = sqrt(results.map { (it.isotropic - isotropicMean) * (it.isotropic - isotropicMean) }.average())
        val anisotropicStd = sqrt(results.map { (it.anisotropic - anisotropicMean) * (it.anisotropic - anisotropicMean) }.average())
        
        var axisDisplay = "UNRELIABLE"
        var axisMean = 0.0
        if (anisotropicMean > 0.02) {
            var sinSum = 0.0
            var cosSum = 0.0
            for (r in results) {
                val rad = r.axis * 2.0 * Math.PI / 180.0
                sinSum += sin(rad)
                cosSum += cos(rad)
            }
            axisMean = atan2(sinSum / results.size, cosSum / results.size) * 180.0 / (2.0 * Math.PI)
            if (axisMean < 0) axisMean += 180.0
            if (axisMean >= 180.0) axisMean -= 180.0
            axisDisplay = String.format("%.0f° SIGNAL", axisMean)
        }
        
        val lastRun = results.last()
        val visualVectorMap = if (lastRun.referencePoints.isNotEmpty()) { 
             drawVectorMapInternal(lastRun, 1f)
        } else null
        
        return@withContext V4Result(
            success = true,
            sphDisplay = "NOT CALIBRATED",
            cylDisplay = "NOT CALIBRATED",
            axisDisplay = axisDisplay,
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
        if (run.refWidth <= 0 || run.refHeight <= 0) {
            return Bitmap.createBitmap(1, 1, Bitmap.Config.ARGB_8888)
        }
        val bitmap = Bitmap.createBitmap(run.refWidth, run.refHeight, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        canvas.drawColor(Color.BLACK)
        
        val paintRef = Paint().apply { color = Color.RED; style = Paint.Style.FILL; isAntiAlias = true }
        val paintLens = Paint().apply { color = Color.GREEN; style = Paint.Style.FILL; isAntiAlias = true }
        val paintArrow = Paint().apply { color = Color.YELLOW; strokeWidth = 2f; style = Paint.Style.STROKE; isAntiAlias = true }
        
        val sizeRef = run.referencePoints.size
        val sizeLens = run.observedPoints.size
        val limit = min(sizeRef, sizeLens)
        
        val paintRejRef = Paint().apply { color = Color.argb(100, 255, 0, 0); style = Paint.Style.FILL; isAntiAlias = true }
        for (pt in run.rejectedReferencePoints) {
            canvas.drawCircle(pt.x.toFloat(), pt.y.toFloat(), 3f, paintRejRef)
        }
        
        val paintRejLens = Paint().apply { color = Color.argb(100, 0, 255, 0); style = Paint.Style.FILL; isAntiAlias = true }
        for (pt in run.unmatchedLensPoints) {
            canvas.drawCircle(pt.x.toFloat(), pt.y.toFloat(), 3f, paintRejLens)
        }
        
        for (i in 0 until limit) {
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
