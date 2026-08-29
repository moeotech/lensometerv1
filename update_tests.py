import re

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'r') as f:
    content = f.read()

new_tests = """
    @Test
    fun testJ_robustness_smoothRadial() {
        val refPts = generateGrid(800.0, 600.0, 30.0)
        val cx = 400.0; val cy = 300.0
        val scale = 1.05
        val lensPts = refPts.map { p ->
            val dx = (p.x - cx) * scale
            val dy = (p.y - cy) * scale
            Point(cx + dx, cy + dy)
        }
        
        val analyzer = V4OpticalAnalyzer(spacing = 30.0, center = Point(cx, cy))
        val result = analyzer.analyzePoints(refPts, lensPts, 800, 600, useRigidFallback = true)
        
        assertTrue("Analysis should succeed", result.success)
        assertEquals("No local outliers should be rejected in smooth field", 0, result.localOutlierRejections)
        assertEquals("No crossing vectors", 0, result.crossingVectorRejections)
        assertTrue("Should be isotropic", result.isotropic > 0.04)
        assertTrue("Anisotropic should be very small", result.anisotropic < 0.01)
    }

    @Test
    fun testK_robustness_smoothAnisotropic() {
        val refPts = generateGrid(800.0, 600.0, 30.0)
        val cx = 400.0; val cy = 300.0
        val scaleX = 1.06
        val scaleY = 1.02
        val lensPts = refPts.map { p ->
            val dx = (p.x - cx) * scaleX
            val dy = (p.y - cy) * scaleY
            Point(cx + dx, cy + dy)
        }
        
        val analyzer = V4OpticalAnalyzer(spacing = 30.0, center = Point(cx, cy))
        val result = analyzer.analyzePoints(refPts, lensPts, 800, 600, useRigidFallback = true)
        
        assertTrue("Analysis should succeed", result.success)
        assertEquals("No local outliers should be rejected", 0, result.localOutlierRejections)
        assertTrue("Should detect anisotropy", result.anisotropic > 0.03)
        assertEquals("L1 should be ~0.06", 0.06, result.lambda1, 0.01)
        assertEquals("L2 should be ~0.02", 0.02, result.lambda2, 0.01)
    }

    @Test
    fun testL_robustness_corruptedCorrespondences() {
        val refPts = generateGrid(800.0, 600.0, 30.0)
        val cx = 400.0; val cy = 300.0
        val scale = 1.04
        
        val cleanLensPts = refPts.map { p ->
            val dx = (p.x - cx) * scale
            val dy = (p.y - cy) * scale
            Point(cx + dx, cy + dy)
        }
        
        // Analyze clean first
        val analyzer = V4OpticalAnalyzer(spacing = 30.0, center = Point(cx, cy))
        val cleanResult = analyzer.analyzePoints(refPts, cleanLensPts, 800, 600, useRigidFallback = true)
        
        // Corrupt a few points (gross local errors)
        val corruptedLensPts = cleanLensPts.toMutableList()
        // Corrupt point index 50
        if (corruptedLensPts.size > 50) {
            corruptedLensPts[50] = Point(corruptedLensPts[50].x + 40.0, corruptedLensPts[50].y - 30.0)
        }
        // Corrupt point index 150
        if (corruptedLensPts.size > 150) {
            corruptedLensPts[150] = Point(corruptedLensPts[150].x - 50.0, corruptedLensPts[150].y + 20.0)
        }
        
        val corruptedResult = analyzer.analyzePoints(refPts, corruptedLensPts, 800, 600, useRigidFallback = true)
        
        assertTrue("Analysis should succeed", corruptedResult.success)
        assertTrue("Should reject some local outliers", corruptedResult.localOutlierRejections >= 2 || corruptedResult.crossingVectorRejections > 0)
        
        // Assert the recovered eigenvalues are approximately the same
        assertEquals("Lambda1 should match despite corruption", cleanResult.lambda1, corruptedResult.lambda1, 0.005)
        assertEquals("Lambda2 should match despite corruption", cleanResult.lambda2, corruptedResult.lambda2, 0.005)
    }

    @Test
    fun testM_robustness_zeroPower() {
        val refPts = generateGrid(800.0, 600.0, 30.0)
        val lensPts = refPts.map { Point(it.x, it.y) }
        
        val analyzer = V4OpticalAnalyzer(spacing = 30.0, center = Point(400.0, 300.0))
        val result = analyzer.analyzePoints(refPts, lensPts, 800, 600, useRigidFallback = true)
        
        assertTrue("Analysis should succeed", result.success)
        assertEquals("L1 should be ~0", 0.0, result.lambda1, 0.001)
        assertEquals("L2 should be ~0", 0.0, result.lambda2, 0.001)
        assertEquals("0 outliers", 0, result.localOutlierRejections)
    }

    @Test
    fun testN_robustness_cameraTranslationRotation() {
        val refPts = generateGrid(800.0, 600.0, 30.0)
        val cx = 400.0; val cy = 300.0
        val theta = 5.0 * Math.PI / 180.0
        val tx = 15.0; val ty = -10.0
        
        val lensPts = refPts.map { p ->
            val dx = p.x - cx
            val dy = p.y - cy
            val nx = dx * cos(theta) - dy * sin(theta) + cx + tx
            val ny = dx * sin(theta) + dy * cos(theta) + cy + ty
            Point(nx, ny)
        }
        
        val analyzer = V4OpticalAnalyzer(spacing = 30.0, center = Point(cx, cy))
        val result = analyzer.analyzePoints(refPts, lensPts, 800, 600, useRigidFallback = true)
        
        assertTrue("Analysis should succeed", result.success)
        assertEquals("L1 should be ~0 since rotation is factored out", 0.0, result.lambda1, 0.001)
        assertEquals("L2 should be ~0 since rotation is factored out", 0.0, result.lambda2, 0.001)
        assertEquals("0 outliers", 0, result.localOutlierRejections)
    }
}
"""

content = re.sub(r'\}\s*$', new_tests, content)

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'w') as f:
    f.write(content)
