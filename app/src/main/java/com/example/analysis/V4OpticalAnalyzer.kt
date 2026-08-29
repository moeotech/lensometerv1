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
    
    val topologyMatchCount: Int = 0,
    val registrationFeatureCount: Int = 0,
    val registrationInliers: Int = 0,
    val registrationRms: Double = 0.0,
    
    val opticalFieldInputCount: Int = 0,
    val opticalFieldRetainedCount: Int = 0,
    val fieldFitRms: Double = 0.0,
    
    val refDotCount: Int = 0,
    val lensDotCount: Int = 0,
    val meanDx: Double = 0.0,
    val meanDy: Double = 0.0,
    val referencePoints: List<Point> = emptyList(),
    val observedPoints: List<Point> = emptyList(),
    val refWidth: Int = 0,
    val refHeight: Int = 0,
    val registrationModel: String = "",
    val registrationRotationDeg: Double = 0.0,
    val registrationTx: Double = 0.0,
    val registrationTy: Double = 0.0,
    val registrationScale: Double = 0.0,
    val candidateMatches: Int = 0,
    val acceptedMatches: Int = 0,
    val matchRejections: Map<String, Int> = emptyMap(),
    val spatialCoveragePct: Double = 0.0,
    val quadrantCoverage: Int = 0,
    val matrixRank: Int = 0,
    val conditionNumber: Double = 0.0,
    val degeneracyStatus: String = "",
    val framesCaptured: Int = 0,
    val framesAccepted: Int = 0,
    val framesRejected: Int = 0,
    val temporalTrackCount: Int = 0,
    val stableTrackCount: Int = 0,
    val medianTrackLifetime: Double = 0.0,
    val rejectedReferencePoints: List<Point> = emptyList(),
    val unmatchedLensPoints: List<Point> = emptyList(),
    val localOutlierRejections: Int = 0,
    val crossingVectorRejections: Int = 0,
    val medianLocalResidual: Double = 0.0,
    val madLocalResidual: Double = 0.0,
    val opticalRejectedReferencePoints: List<Point> = emptyList(),
    val opticalRejectedObservedPoints: List<Point> = emptyList()
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
    val registrationInliers: Int = 0,
    val fieldFitRms: Double = 0.0,
    val refDotCount: Int = 0,
    val lensDotCount: Int = 0,
    val meanDx: Double = 0.0,
    val meanDy: Double = 0.0,
    val visualVectorMap: Bitmap? = null,
    val lastRunResult: V4RunResult? = null,
    val registrationModel: String = "",
    val registrationRotationDeg: Double = 0.0,
    val registrationTx: Double = 0.0,
    val registrationTy: Double = 0.0,
    val registrationScale: Double = 0.0
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
    val unmatchedLensPoints: List<Point> = emptyList(),
    val localOutlierRejections: Int = 0,
    val crossingVectorRejections: Int = 0,
    val medianLocalResidual: Double = 0.0,
    val madLocalResidual: Double = 0.0,
    val opticalRejectedReferencePoints: List<Point> = emptyList(),
    val opticalRejectedObservedPoints: List<Point> = emptyList()
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


    private fun estimateStrictRigid(srcPts: List<Point>, dstPts: List<Point>, ransacThresh: Double): Pair<Mat, Mat> {
        val srcMat = MatOfPoint2f().apply { fromList(srcPts) }
        val dstMat = MatOfPoint2f().apply { fromList(dstPts) }
        val mask = Mat()
        val partial = Calib3d.estimateAffinePartial2D(srcMat, dstMat, mask, Calib3d.RANSAC, ransacThresh)
        if (partial.empty()) return Pair(Mat(), mask)

        val maskArray = ByteArray(mask.rows() * mask.cols())
        mask.get(0, 0, maskArray)

        val inlierSrc = mutableListOf<Point>()
        val inlierDst = mutableListOf<Point>()
        for (i in srcPts.indices) {
            if (maskArray[i].toInt() != 0) {
                inlierSrc.add(srcPts[i])
                inlierDst.add(dstPts[i])
            }
        }

        if (inlierSrc.size < 2) return Pair(Mat(), mask)

        var cxSrc = 0.0; var cySrc = 0.0
        var cxDst = 0.0; var cyDst = 0.0
        val N = inlierSrc.size
        for (i in inlierSrc.indices) {
            cxSrc += inlierSrc[i].x; cySrc += inlierSrc[i].y
            cxDst += inlierDst[i].x; cyDst += inlierDst[i].y
        }
        cxSrc /= N; cySrc /= N; cxDst /= N; cyDst /= N

        var h00 = 0.0; var h01 = 0.0; var h10 = 0.0; var h11 = 0.0
        for (i in inlierSrc.indices) {
            val sx = inlierSrc[i].x - cxSrc
            val sy = inlierSrc[i].y - cySrc
            val dx = inlierDst[i].x - cxDst
            val dy = inlierDst[i].y - cyDst
            h00 += sx * dx; h01 += sx * dy
            h10 += sy * dx; h11 += sy * dy
        }

        val H = Mat(2, 2, CvType.CV_64F)
        H.put(0, 0, h00, h01, h10, h11)
        val w = Mat(); val u = Mat(); val vt = Mat()
        Core.SVDecomp(H, w, u, vt)

        val R = Mat(2, 2, CvType.CV_64F)
        Core.gemm(vt.t(), u.t(), 1.0, Mat(), 0.0, R)

        if (Core.determinant(R) < 0) {
            val vtFixed = vt.clone()
            vtFixed.put(1, 0, -vtFixed.get(1, 0)[0], -vtFixed.get(1, 1)[0])
            Core.gemm(vtFixed.t(), u.t(), 1.0, Mat(), 0.0, R)
        }

        val r00 = R.get(0, 0)[0]; val r01 = R.get(0, 1)[0]
        val r10 = R.get(1, 0)[0]; val r11 = R.get(1, 1)[0]

        val tx = cxDst - (r00 * cxSrc + r01 * cySrc)
        val ty = cyDst - (r10 * cxSrc + r11 * cySrc)

        val rigidTransform = Mat(2, 3, CvType.CV_64F)
        rigidTransform.put(0, 0, r00, r01, tx, r10, r11, ty)

        return Pair(rigidTransform, mask)
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
            
            val (transform, mask) = estimateStrictRigid(matchedCurr, matchedBase, 3.0)
            
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
            
            val useRigidFallback = anchorRef.size < 4
            
            val regSrc: List<Point>
            val regDst: List<Point>
            if (useRigidFallback) {
                regSrc = matchedLens
                regDst = matchedRef
            } else {
                regSrc = anchorLens
                regDst = anchorRef
            }
            
            val ransacThresh = if (useRigidFallback) max(15.0, spacing * 0.8) else max(5.0, spacing * 0.4)
            
            if (regSrc.size < 4) {
                return V4RunResult(success = false, errorMessage = "REGISTRATION UNSTABLE (Not enough points)", candidateMatches = matchedRef.size, matchRejections = rejections)
            }
            
            val (transformMat, mask) = estimateStrictRigid(regSrc, regDst, ransacThresh)
            
            if (transformMat.empty()) {
                rejections["registration_inconsistency"] = rejections.getOrDefault("registration_inconsistency", 0) + matchedRef.size
                return V4RunResult(success = false, errorMessage = "Registration failed", candidateMatches = matchedRef.size, matchRejections = rejections)
            }
            
            val r00 = transformMat.get(0, 0)[0]
            val r10 = transformMat.get(1, 0)[0]
            val registrationRotationDeg = atan2(r10, r00) * 180.0 / Math.PI
            val registrationTx = transformMat.get(0, 2)[0]
            val registrationTy = transformMat.get(1, 2)[0]
            val registrationModel = if (useRigidFallback) "RIGID_FALLBACK" else "RIGID_ANCHOR"
            
            val maskArray = ByteArray(mask.rows() * mask.cols())
            mask.get(0, 0, maskArray)
            inliersCount = maskArray.count { it.toInt() != 0 }
            
            val ptsToMeasureRef = matchedRef.toMutableList()
            val ptsToMeasureLens = matchedLens.toMutableList()
            
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
            // Robust Optical Vector Field Filter
            val displacements = ptsToMeasureRef.zip(transformedLens).map { Point(it.second.x - it.first.x, it.second.y - it.first.y) }
            val searchRadius = spacing * 1.8
            val minNeighbors = 3
            val localOutlierIndices = mutableSetOf<Int>()
            val crossingIndices = mutableSetOf<Int>()

            val localResiduals = mutableListOf<Double>()

            for (i in ptsToMeasureRef.indices) {
                val refPt = ptsToMeasureRef[i]
                val disp = displacements[i]
                val dstPt = transformedLens[i]
                
                val neighborIndices = mutableListOf<Int>()
                for (j in ptsToMeasureRef.indices) {
                    if (i == j) continue
                    val distSq = (refPt.x - ptsToMeasureRef[j].x).pow(2) + (refPt.y - ptsToMeasureRef[j].y).pow(2)
                    if (distSq < searchRadius * searchRadius) {
                        neighborIndices.add(j)
                    }
                }
                
                var crossing = false
                for (j in neighborIndices) {
                    val nRefPt = ptsToMeasureRef[j]
                    val nDstPt = transformedLens[j]
                    
                    val refDist = hypot(refPt.x - nRefPt.x, refPt.y - nRefPt.y)
                    val dstDist = hypot(dstPt.x - nDstPt.x, dstPt.y - nDstPt.y)
                    
                    if (dstDist < refDist * 0.3) {
                        crossing = true
                        break
                    }
                    
                    val refVecX = nRefPt.x - refPt.x
                    val refVecY = nRefPt.y - refPt.y
                    val dstVecX = nDstPt.x - dstPt.x
                    val dstVecY = nDstPt.y - dstPt.y
                    val dot = refVecX * dstVecX + refVecY * dstVecY
                    if (dot < 0) { 
                        crossing = true
                        break
                    }
                }
                
                if (crossing) {
                    crossingIndices.add(i)
                    continue
                }
                
                if (neighborIndices.size >= minNeighbors) {
                    val nDispsX = neighborIndices.map { displacements[it].x }.sorted()
                    val nDispsY = neighborIndices.map { displacements[it].y }.sorted()
                    
                    val medX = nDispsX[nDispsX.size / 2]
                    val medY = nDispsY[nDispsY.size / 2]
                    
                    val nDistToMed = neighborIndices.map { 
                        hypot(displacements[it].x - medX, displacements[it].y - medY)
                    }.sorted()
                    val mad = nDistToMed[nDistToMed.size / 2]
                    
                    val distToMed = hypot(disp.x - medX, disp.y - medY)
                    localResiduals.add(distToMed)
                    
                    val thresh = max(mad * 4.0, spacing * 0.15)
                    if (distToMed > thresh) {
                        localOutlierIndices.add(i)
                    }
                }
            }

            val finalRefPts = mutableListOf<Point>()
            val finalLensPts = mutableListOf<Point>()
            val optRejectedRefPts = mutableListOf<Point>()
            val optRejectedLensPts = mutableListOf<Point>()

            for (i in ptsToMeasureRef.indices) {
                if (crossingIndices.contains(i) || localOutlierIndices.contains(i)) {
                    optRejectedRefPts.add(ptsToMeasureRef[i])
                    optRejectedLensPts.add(transformedLens[i])
                } else {
                    finalRefPts.add(ptsToMeasureRef[i])
                    finalLensPts.add(transformedLens[i])
                }
            }

            ptsToMeasureRef.clear()
            ptsToMeasureRef.addAll(finalRefPts)
            
            val filteredTransformedLens = finalLensPts
            
            val medianLocalRes = if (localResiduals.isNotEmpty()) localResiduals.sorted()[localResiduals.size / 2] else 0.0
            val madLocalRes = if (localResiduals.isNotEmpty()) {
                val m = medianLocalRes
                localResiduals.map { abs(it - m) }.sorted()[localResiduals.size / 2]
            } else 0.0

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
                
                B.put(i, 0, filteredTransformedLens[i].x - ptsToMeasureRef[i].x)
                B.put(i, 1, filteredTransformedLens[i].y - ptsToMeasureRef[i].y)
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
            
            val s00 = j00
            val s11 = j11
            val s01 = 0.5 * (j01 + j10)
            
            val trace = s00 + s11
            val delta = sqrt(((s00 - s11) / 2.0) * ((s00 - s11) / 2.0) + s01 * s01)
            
            var l1 = trace / 2.0 + delta
            var l2 = trace / 2.0 - delta
            
            if (abs(l2) > abs(l1)) {
                val temp = l1; l1 = l2; l2 = temp
            }
            
            val iso = (l1 + l2) / 2.0
            val aniso = abs(l1 - l2)
            
            var axisRad = 0.0
            if (abs(s01) > 1e-6 || abs(s00 - s11) > 1e-6) {
                axisRad = 0.5 * atan2(2.0 * s01, s00 - s11)
            }
            var axisDeg = axisRad * 180.0 / PI
            while (axisDeg < 0.0) axisDeg += 180.0
            while (axisDeg >= 180.0) axisDeg -= 180.0
            
            var sumDx = 0.0; var sumDy = 0.0
            for (i in 0 until numMeas) {
                sumDx += (filteredTransformedLens[i].x - ptsToMeasureRef[i].x)
                sumDy += (filteredTransformedLens[i].y - ptsToMeasureRef[i].y)
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
                observedPoints = filteredTransformedLens,
                localOutlierRejections = localOutlierIndices.size,
                crossingVectorRejections = crossingIndices.size,
                medianLocalResidual = medianLocalRes,
                madLocalResidual = madLocalRes,
                opticalRejectedReferencePoints = optRejectedRefPts,
                opticalRejectedObservedPoints = optRejectedLensPts,
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
            )
        } catch (e: Exception) {
            Log.e("V4OpticalAnalyzer", "AnalyzePoints failed", e)
            return V4RunResult(success = false, errorMessage = "Exception: ${e.message}")
        }
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

        val cvThreshold = 0.30
        val minSignal = 0.05
        
        fun checkCv(mean: Double, std: Double, name: String): String? {
            if (Math.abs(mean) > minSignal) {
                val cv = std / Math.abs(mean)
                if (cv > cvThreshold) return "$name CV=${String.format("%.2f", cv)}"
            }
            return null
        }
        
        val fails = listOfNotNull(
            checkCv(lambda1Mean, lambda1Std, "L1"),
            checkCv(lambda2Mean, lambda2Std, "L2"),
            checkCv(isotropicMean, isotropicStd, "ISO"),
            checkCv(anisotropicMean, anisotropicStd, "ANISO")
        )
        
        val l1_vals = results.map { it.lambda1 }.sorted()
        val spreadFails = l1_vals.last() - l1_vals.first() > 0.15
        
        if (fails.isNotEmpty() || spreadFails) {
            val reason = if (fails.isNotEmpty()) fails.joinToString(", ") else "Lambda1 spread > 0.15"
            return@withContext V4Result(success = false, errorMessage = "OPTICAL REPEATABILITY: FAILED ($reason)", allRuns = results, lastRunResult = results.last())
        }

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
            registrationInliers = lastRun.registrationInliers,
            fieldFitRms = lastRun.fieldFitRms,
            refDotCount = lastRun.refDotCount,
            lensDotCount = lastRun.lensDotCount,
            meanDx = lastRun.meanDx,
            meanDy = lastRun.meanDy,
            visualVectorMap = visualVectorMap,
            lastRunResult = lastRun
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
        
        val paintOptRejRef = Paint().apply { color = Color.GRAY; style = Paint.Style.FILL; isAntiAlias = true }
        val paintOptRejLens = Paint().apply { color = Color.MAGENTA; style = Paint.Style.FILL; isAntiAlias = true }
        val paintOptRejArrow = Paint().apply { color = Color.GRAY; strokeWidth = 1f; style = Paint.Style.STROKE; isAntiAlias = true }

        val sizeOptRej = min(run.opticalRejectedReferencePoints.size, run.opticalRejectedObservedPoints.size)
        for (i in 0 until sizeOptRej) {
            val refPt = run.opticalRejectedReferencePoints[i]
            val lensPt = run.opticalRejectedObservedPoints[i]
            
            canvas.drawCircle(refPt.x.toFloat(), refPt.y.toFloat(), 3f, paintOptRejRef)
            
            val dx = (lensPt.x - refPt.x) * mag
            val dy = (lensPt.y - refPt.y) * mag
            
            canvas.drawCircle((refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), 3f, paintOptRejLens)
            canvas.drawLine(refPt.x.toFloat(), refPt.y.toFloat(), (refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), paintOptRejArrow)
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
