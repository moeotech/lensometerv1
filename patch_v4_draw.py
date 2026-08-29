import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r'val sizeOptRej = min\(run\.opticalRejectedReferencePoints\.size, run\.opticalRejectedObservedPoints\.size\)\n\s*for \(i in 0 until sizeOptRej\) \{.*?\n\s*\}\n\s*for \(i in 0 until limit\) \{.*?\n\s*\}'

replacement = r"""
        val paintLocalRejArrow = Paint().apply { color = Color.argb(200, 255, 165, 0); strokeWidth = 1f; style = Paint.Style.STROKE; isAntiAlias = true } // ORANGE
        val paintCrossRejArrow = Paint().apply { color = Color.MAGENTA; strokeWidth = 1.5f; style = Paint.Style.STROKE; isAntiAlias = true }
        
        for (pair in run.pairs) {
            val refPt = pair.reference
            val lensPt = pair.observed
            val dx = (lensPt.x - refPt.x) * mag
            val dy = (lensPt.y - refPt.y) * mag
            
            if (pair.status == "RETAINED") {
                canvas.drawCircle(refPt.x.toFloat(), refPt.y.toFloat(), 3f, paintRef)
                canvas.drawCircle((refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), 3f, paintLens)
                canvas.drawLine(refPt.x.toFloat(), refPt.y.toFloat(), (refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), paintArrow)
            } else if (pair.status == "LOCAL_OUTLIER") {
                canvas.drawCircle(refPt.x.toFloat(), refPt.y.toFloat(), 3f, paintOptRejRef)
                canvas.drawCircle((refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), 3f, paintOptRejLens)
                canvas.drawLine(refPt.x.toFloat(), refPt.y.toFloat(), (refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), paintLocalRejArrow)
            } else { // CROSSING_REJECTED or GLOBAL_OUTLIER
                canvas.drawCircle(refPt.x.toFloat(), refPt.y.toFloat(), 3f, paintOptRejRef)
                canvas.drawCircle((refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), 3f, paintOptRejLens)
                canvas.drawLine(refPt.x.toFloat(), refPt.y.toFloat(), (refPt.x + dx).toFloat(), (refPt.y + dy).toFloat(), paintCrossRejArrow)
            }
        }
"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
