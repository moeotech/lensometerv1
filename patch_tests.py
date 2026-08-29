import re

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'r') as f:
    content = f.read()

new_tests = """
    @Test
    fun testInsufficientPoints() = runBlocking {
        val matchedRef = listOf(Point(10.0, 10.0), Point(20.0, 20.0))
        val matchedLens = listOf(Point(11.0, 11.0), Point(21.0, 21.0))
        val result = V4OpticalAnalyzer.analyzePoints(matchedRef, matchedLens, 640.0, 480.0)
        
        // Should fail due to insufficient points without crashing
        assertTrue(!result.success)
        assertTrue(result.errorMessage.contains("Insufficient matched points"))
    }

    @Test
    fun testCollinearPoints() = runBlocking {
        val matchedRef = mutableListOf<Point>()
        val matchedLens = mutableListOf<Point>()
        // Generate 10 points all on a single line
        for (i in 0 until 10) {
            matchedRef.add(Point(100.0 + i * 10.0, 100.0))
            matchedLens.add(Point(100.0 + i * 11.0, 100.0))
        }
        val result = V4OpticalAnalyzer.analyzePoints(matchedRef, matchedLens, 640.0, 480.0)
        
        // Should fail due to degeneracy (rank deficient)
        assertTrue(!result.success)
        assertTrue(result.errorMessage.contains("Degenerate") || result.errorMessage.contains("RANK_DEFICIENT"))
    }

    @Test
    fun testNaNValues() = runBlocking {
        val matchedRef = mutableListOf<Point>()
        val matchedLens = mutableListOf<Point>()
        for (i in 0 until 10) {
            matchedRef.add(Point(100.0 + i * 10.0, 100.0 + i * 5.0))
            matchedLens.add(Point(Double.NaN, Double.NaN))
        }
        val result = V4OpticalAnalyzer.analyzePoints(matchedRef, matchedLens, 640.0, 480.0)
        
        // Should fail cleanly, possibly in registration or later, without crashing
        assertTrue(!result.success)
    }
"""

content = content.replace("}", new_tests + "\n}")

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'w') as f:
    f.write(content)
