import re

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'r') as f:
    content = f.read()

new_test = """
    @Test
    fun testQ_pairedIntegrity() {
        val w = 800.0; val h = 600.0
        val refPts = generateGrid(w, h, 30.0)
        val lensPts = refPts.map { Point(it.x + 1.0, it.y - 1.0) }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, 30.0)
        assertTrue(result.success)
        assertEquals("Pairs size should match returned retained point lists sizes", result.referencePoints.size, result.observedPoints.size)
        assertEquals("Pairs size should match retained pairs", result.pairs.count { it.status == "RETAINED" }, result.referencePoints.size)
    }
}
"""

content = re.sub(r'\}\s*$', new_test, content)

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'w') as f:
    f.write(content)
