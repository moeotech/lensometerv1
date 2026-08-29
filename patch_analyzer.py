import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# 1. Add fields to V4RunResult
result_replacement = """    val stableTrackCount: Int = 0,
    val medianTrackLifetime: Double = 0.0,
    val rejectedReferencePoints: List<Point> = emptyList(),
    val unmatchedLensPoints: List<Point> = emptyList()
)"""
content = content.replace("    val stableTrackCount: Int = 0,\n    val medianTrackLifetime: Double = 0.0\n)", result_replacement)

# 2. Add assignGridTopology function
grid_func = """
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

    suspend fun analyze("""

content = content.replace("    suspend fun analyze(", grid_func)

# 3. Rewrite the match generation in analyze()
old_match = """            val binSize = spacing * 0.2
            val histogram = HashMap<Pair<Int, Int>, Int>()
            for (ptRef in baseRefPoints) {
                for (ptLens in baseLensPoints) {
                    val dx = ptLens.x - ptRef.x
                    val dy = ptLens.y - ptRef.y
                    if (hypot(dx, dy) < 200.0) {
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
            
            val candidateRef = mutableListOf<Point>()
            val candidateLens = mutableListOf<Point>()
            val usedLens = mutableSetOf<Int>()
            
            for (ptRef in baseRefPoints) {
                val shiftedX = ptRef.x + globalTx
                val shiftedY = ptRef.y + globalTy
                
                var bestDist = Double.MAX_VALUE
                var bestIdx = -1
                for (j in baseLensPoints.indices) {
                    val ptLens = baseLensPoints[j]
                    val dist = hypot(ptLens.x - shiftedX, ptLens.y - shiftedY)
                    if (dist < bestDist) {
                        bestDist = dist
                        bestIdx = j
                    }
                }
                
                if (bestIdx != -1) {
                    if (bestDist < spacing * 0.6) {
                        if (usedLens.contains(bestIdx)) {
                            rejections["duplicate_match"] = rejections.getOrDefault("duplicate_match", 0) + 1
                        } else {
                            usedLens.add(bestIdx)
                            candidateRef.add(ptRef)
                            candidateLens.add(baseLensPoints[bestIdx])
                        }
                    } else {
                        rejections["distance_gate"] = rejections.getOrDefault("distance_gate", 0) + 1
                    }
                } else {
                    rejections["other"] = rejections.getOrDefault("other", 0) + 1
                }
            }
            
            val w = noLensFrames[0].width.toDouble()
            val h = noLensFrames[0].height.toDouble()"""

new_match = """            val w = noLensFrames[0].width.toDouble()
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
            rejections["Quad4_Matches"] = q4"""

content = content.replace(old_match, new_match)

# 4. Modify the return call in analyze() to pass the rejected points
ret_old = """            return@withContext res.copy(
                framesCaptured = withLensFrames.size,
                framesAccepted = lensAgg.accepted,
                framesRejected = lensAgg.rejected,
                temporalTrackCount = lensAgg.points.size,
                stableTrackCount = lensAgg.stableTrackCount,
                medianTrackLifetime = lensAgg.medianTrackLifetime
            )"""
            
ret_new = """            return@withContext res.copy(
                framesCaptured = withLensFrames.size,
                framesAccepted = lensAgg.accepted,
                framesRejected = lensAgg.rejected,
                temporalTrackCount = lensAgg.points.size,
                stableTrackCount = lensAgg.stableTrackCount,
                medianTrackLifetime = lensAgg.medianTrackLifetime,
                rejectedReferencePoints = rejectedRefs,
                unmatchedLensPoints = unmatchedLens
            )"""

content = content.replace(ret_old, ret_new)

# 5. Update drawVectorMapInternal
draw_old = """        for (i in 0 until limit) {
            val refPt = run.referencePoints[i]
            val lensPt = run.observedPoints[i]
            
            canvas.drawCircle(refPt.x.toFloat(), refPt.y.toFloat(), 3f, paintRef)
            
            val dx = (lensPt.x - refPt.x) * mag
            val dy = (lensPt.y - refPt.y) * mag
            
            canvas.drawCircle((refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), 3f, paintLens)
            canvas.drawLine(refPt.x.toFloat(), refPt.y.toFloat(), (refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), paintArrow)
        }
        
        return bitmap"""

draw_new = """        val paintRejRef = Paint().apply { color = Color.argb(100, 255, 0, 0); style = Paint.Style.FILL; isAntiAlias = true }
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
        
        return bitmap"""
        
content = content.replace(draw_old, draw_new)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)

