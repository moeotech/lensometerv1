import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

robust_logic = """
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

            // IRLS for robust optical field fit"""

content = re.sub(r'\s*// IRLS for robust optical field fit', robust_logic, content)

# update transformedLens in B matrix
content = re.sub(r'transformedLens\[i\]\.x - ptsToMeasureRef\[i\]\.x', r'filteredTransformedLens[i].x - ptsToMeasureRef[i].x', content)
content = re.sub(r'transformedLens\[i\]\.y - ptsToMeasureRef\[i\]\.y', r'filteredTransformedLens[i].y - ptsToMeasureRef[i].y', content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
