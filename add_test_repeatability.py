import re

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'r') as f:
    content = f.read()

new_test = """
    @Test
    fun testO_repeatabilityGateUnstable() {
        val w = 800.0; val h = 600.0
        val refPts = generateGrid(w, h, 30.0)
        
        // Run 1: Isotropic 0.01
        val lensPts1 = refPts.map { Point(it.x + (it.x - 400)*0.01, it.y + (it.y - 300)*0.01) }
        val r1 = V4OpticalAnalyzer.analyzePoints(refPts, lensPts1, w, h, refPts.size, lensPts1.size, 30.0)
        
        // Run 2: Isotropic 0.03
        val lensPts2 = refPts.map { Point(it.x + (it.x - 400)*0.03, it.y + (it.y - 300)*0.03) }
        val r2 = V4OpticalAnalyzer.analyzePoints(refPts, lensPts2, w, h, refPts.size, lensPts2.size, 30.0)
        
        // Run 3: Isotropic -0.01
        val lensPts3 = refPts.map { Point(it.x - (it.x - 400)*0.01, it.y - (it.y - 300)*0.01) }
        val r3 = V4OpticalAnalyzer.analyzePoints(refPts, lensPts3, w, h, refPts.size, lensPts3.size, 30.0)
        
        val finalResult = V4OpticalAnalyzer.checkRepeatability(listOf(r1, r2, r3))
        
        assertFalse("Measurement should be unstable", finalResult.success)
        assertTrue(finalResult.errorMessage.contains("MEASUREMENT UNSTABLE"))
    }
}
"""

content = re.sub(r'\}\s*$', new_test, content)

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'w') as f:
    f.write(content)
