import re

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'r') as f:
    content = f.read()

tests = """
    @Test
    fun testR_motionCorrection_pureTranslation() {
        val w = 800.0; val h = 600.0
        val refPts = generateGrid(w, h, 30.0)
        
        // Pure translation: dx = 5.0, dy = -3.0
        val lensPts = refPts.map { Point(it.x + 5.0, it.y - 3.0) }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, 30.0)
        assertTrue(result.success)
        
        // Global motion should perfectly capture translation
        assertEquals(5.0, result.globalMotionX, 0.05)
        assertEquals(-3.0, result.globalMotionY, 0.05)
        
        // Corrected optical field should be near zero
        assertEquals(0.0, result.correctedDispMax, 0.05)
        assertEquals(0.0, result.lambda1, 0.001)
        assertEquals(0.0, result.lambda2, 0.001)
    }

    @Test
    fun testS_motionCorrection_pureRadial() {
        val w = 800.0; val h = 600.0
        val refPts = generateGrid(w, h, 30.0)
        
        // Pure radial: k = 0.01 (isotropic)
        val k = 0.01
        val lensPts = refPts.map { 
            val cx = it.x - 400.0
            val cy = it.y - 300.0
            Point(it.x + cx * k, it.y + cy * k) 
        }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, 30.0)
        assertTrue(result.success)
        
        // Global motion should be near zero since radial is symmetric
        assertEquals(0.0, result.globalMotionX, 0.5)
        assertEquals(0.0, result.globalMotionY, 0.5)
        
        // Lambda should match k
        assertEquals(k, result.lambda1, 0.005)
        assertEquals(k, result.lambda2, 0.005)
    }

    @Test
    fun testT_motionCorrection_translationAndRadial() {
        val w = 800.0; val h = 600.0
        val refPts = generateGrid(w, h, 30.0)
        
        // Radial + Translation
        val k = 0.01
        val tx = 4.0
        val ty = -2.0
        
        val lensPts1 = refPts.map { 
            val cx = it.x - 400.0
            val cy = it.y - 300.0
            Point(it.x + cx * k, it.y + cy * k) 
        }
        val result1 = V4OpticalAnalyzer.analyzePoints(refPts, lensPts1, w, h, refPts.size, lensPts1.size, 30.0)
        
        val lensPts2 = refPts.map { 
            val cx = it.x - 400.0
            val cy = it.y - 300.0
            Point(it.x + cx * k + tx, it.y + cy * k + ty) 
        }
        val result2 = V4OpticalAnalyzer.analyzePoints(refPts, lensPts2, w, h, refPts.size, lensPts2.size, 30.0)
        
        assertTrue(result1.success)
        assertTrue(result2.success)
        
        // Result2 should recover translation
        assertEquals(tx, result2.globalMotionX, 0.5)
        assertEquals(ty, result2.globalMotionY, 0.5)
        
        // Both should have roughly same lambda
        assertEquals(result1.lambda1, result2.lambda1, 0.005)
        assertEquals(result1.lambda2, result2.lambda2, 0.005)
    }

    @Test
    fun testU_motionCorrection_anisotropic() {
        val w = 800.0; val h = 600.0
        val refPts = generateGrid(w, h, 30.0)
        
        // Anisotropic + Translation
        val kx = 0.015
        val ky = 0.005
        val tx = -3.0
        val ty = 2.0
        
        val lensPts = refPts.map { 
            val cx = it.x - 400.0
            val cy = it.y - 300.0
            Point(it.x + cx * kx + tx, it.y + cy * ky + ty) 
        }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, 30.0)
        assertTrue(result.success)
        
        assertEquals(tx, result.globalMotionX, 0.5)
        assertEquals(ty, result.globalMotionY, 0.5)
        
        assertEquals(kx, result.lambda1, 0.005)
        assertEquals(ky, result.lambda2, 0.005)
    }
}
"""

content = re.sub(r'\}\s*$', tests, content)

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'w') as f:
    f.write(content)
