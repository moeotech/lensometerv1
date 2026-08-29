import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

draw_pattern = r'for \(i in 0 until limit\) \{\s*val refPt = run\.referencePoints\[i\].*?canvas\.drawLine\(refPt\.x\.toFloat\(\), refPt\.y\.toFloat\(\), \(refPt\.x \+ dx\)\.toFloat\(\), \(refPt\.y \+ dy\)\.toFloat\(\), paintArrow\)\s*\}'
draw_replacement = r"""val paintOptRejRef = Paint().apply { color = Color.GRAY; style = Paint.Style.FILL; isAntiAlias = true }
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
        }"""

content = re.sub(draw_pattern, draw_replacement, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
