import re

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'r') as f:
    content = f.read()

new_test = """
    @Test
    fun testP_robustness_grossLongVectorRejected() {
        val w = 800.0; val h = 600.0
        val refPts = generateGrid(w, h, 30.0)
        
        val lensPts = refPts.map { Point(it.x + (it.x - 400)*0.01, it.y + (it.y - 300)*0.01) }.toMutableList()
        // Inject a gross long vector
        if (lensPts.size > 100) {
            lensPts[100] = Point(lensPts[100].x + 200.0, lensPts[100].y - 200.0)
        }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, 30.0)
        assertTrue(result.success)
        assertTrue(result.opticalRejectedObservedPoints.isNotEmpty())
        assertTrue(result.localOutlierRejections > 0 || result.crossingVectorRejections > 0 || result.pairs.any { it.status == "GLOBAL_OUTLIER" })
    }
}
"""

content = re.sub(r'\}\s*$', new_test, content)

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'w') as f:
    f.write(content)
