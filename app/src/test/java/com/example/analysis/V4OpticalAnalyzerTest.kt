package com.example.analysis

import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.opencv.core.Point
import org.opencv.android.OpenCVLoader

@RunWith(RobolectricTestRunner::class)
@Config(manifest=Config.NONE)
class V4OpticalAnalyzerTest {

    init {
        OpenCVLoader.initLocal()
    }

    private fun generateGrid(w: Double, h: Double, spacing: Double): List<Point> {
        val pts = mutableListOf<Point>()
        var y = spacing
        while (y < h - spacing) {
            var x = spacing
            while (x < w - spacing) {
                pts.add(Point(x, y))
                x += spacing
            }
            y += spacing
        }
        return pts
    }

    @Test
    fun testCameraTranslationAndLensIsotropicScaling() {
        val w = 1000.0
        val h = 1000.0
        val spacing = 30.0
        val refPts = generateGrid(w, h, spacing)
        
        val cx = w / 2.0
        val cy = h / 2.0
        val rMax = 500.0
        val innerRadiusSq = (rMax * 0.7) * (rMax * 0.7)
        
        val lensPts = mutableListOf<Point>()
        for (pt in refPts) {
            val dSq = (pt.x - cx) * (pt.x - cx) + (pt.y - cy) * (pt.y - cy)
            if (dSq > innerRadiusSq) {
                // Outer anchors: apply camera translation (dx=10, dy=-15)
                lensPts.add(Point(pt.x + 10.0, pt.y - 15.0))
            } else {
                // Inner points: apply camera translation + isotropic scaling centered at cx, cy
                val scale = 1.05
                val scaledX = cx + (pt.x - cx) * scale
                val scaledY = cy + (pt.y - cy) * scale
                lensPts.add(Point(scaledX + 10.0, scaledY - 15.0))
            }
        }
        
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, spacing)
        
        assertTrue("Run should succeed", result.success)
        assertTrue("Scale should not be ambiguous (we have anchors)", !result.globalScaleAmbiguous)
        
        // Isotropic scaling of 1.05 means dx = 0.05 * x
        // The optical field u(x,y) = 0.05*x, v(x,y) = 0.05*y
        // Lambda1 and Lambda2 should both be ~ 0.05
        assertEquals(0.05, result.lambda1, 0.01)
        assertEquals(0.05, result.lambda2, 0.01)
        assertEquals(0.05, result.isotropic, 0.01)
        assertEquals(0.0, result.anisotropic, 0.01)
        
        // All measurement points should be retained
        val innerCount = refPts.count { pt -> 
            val dSq = (pt.x - cx) * (pt.x - cx) + (pt.y - cy) * (pt.y - cy)
            dSq <= innerRadiusSq 
        }
        assertEquals(innerCount, result.opticalFieldRetainedCount)
    }

    @Test
    fun testCameraRotationAndAnisotropicDeformation() {
        val w = 1000.0
        val h = 1000.0
        val spacing = 30.0
        val refPts = generateGrid(w, h, spacing)
        
        val cx = w / 2.0
        val cy = h / 2.0
        val rMax = 500.0
        val innerRadiusSq = (rMax * 0.7) * (rMax * 0.7)
        
        val theta = Math.toRadians(5.0) // 5 degrees rotation
        val cosT = Math.cos(theta)
        val sinT = Math.sin(theta)
        
        val lensPts = mutableListOf<Point>()
        for (pt in refPts) {
            val dSq = (pt.x - cx) * (pt.x - cx) + (pt.y - cy) * (pt.y - cy)
            
            // Camera rotation
            val dxC = pt.x - cx
            val dyC = pt.y - cy
            var rotX = cx + dxC * cosT - dyC * sinT
            var rotY = cy + dxC * sinT + dyC * cosT
            
            if (dSq > innerRadiusSq) {
                lensPts.add(Point(rotX, rotY))
            } else {
                // Anisotropic deformation on top of camera rotation
                // Lambda1 = 0.08, Lambda2 = -0.02
                val u = rotX + dxC * 0.08
                val v = rotY + dyC * -0.02
                lensPts.add(Point(u, v))
            }
        }
        
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, spacing)
        
        assertTrue("Run should succeed", result.success)
        
        assertEquals(0.08, result.lambda1, 0.01)
        assertEquals(-0.02, result.lambda2, 0.01)
        assertEquals(0.03, result.isotropic, 0.01)
        assertEquals(0.05, result.anisotropic, 0.01)
    }
    
    @Test
    fun testVerifyRansacMaskNotUsedForOpticalMembership() {
        // If we use rigid fallback (no anchors), the registration RANSAC will only keep a subset
        // We want to ensure all points are passed to the optical field fitter.
        
        val w = 1000.0
        val h = 1000.0
        val spacing = 30.0
        // Small grid, < 15 anchors so rigid fallback triggers
        val refPts = generateGrid(300.0, 300.0, spacing) // 81 points
        
        val cx = 150.0
        val cy = 150.0
        
        val lensPts = mutableListOf<Point>()
        // Introduce a spherical distortion
        for (pt in refPts) {
            val dx = pt.x - cx
            val dy = pt.y - cy
            // L1 = 0.1, L2 = 0.1
            lensPts.add(Point(pt.x + dx * 0.1, pt.y + dy * 0.1))
        }
        
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, 300.0, 300.0, refPts.size, lensPts.size, spacing)
        
        assertTrue(result.success)
        assertTrue(result.globalScaleAmbiguous) // Because no anchors
        
        // RANSAC inliers will be around ~30-40, but retained points should be ~81
        // (The IRLS should keep most if they fit the affine model smoothly)
        assertTrue(result.registrationInliers < refPts.size)
        assertEquals(refPts.size, result.opticalFieldRetainedCount)
    }
    
    @Test
    fun testRobustnessToMismatches() {
        val w = 1000.0
        val h = 1000.0
        val spacing = 30.0
        val refPts = generateGrid(w, h, spacing)
        
        val cx = w / 2.0
        val cy = h / 2.0
        val rMax = 500.0
        val innerRadiusSq = (rMax * 0.7) * (rMax * 0.7)
        
        val lensPts = mutableListOf<Point>()
        for (pt in refPts) {
            val dSq = (pt.x - cx) * (pt.x - cx) + (pt.y - cy) * (pt.y - cy)
            if (dSq > innerRadiusSq) {
                lensPts.add(Point(pt.x, pt.y))
            } else {
                val dx = pt.x - cx
                val dy = pt.y - cy
                lensPts.add(Point(pt.x + dx * 0.05, pt.y + dy * 0.05))
            }
        }
        
        // Corrupt 5 points inside the inner region
        var corrupted = 0
        val innerPts = refPts.indices.filter { i -> 
            val pt = refPts[i]
            val dSq = (pt.x - cx) * (pt.x - cx) + (pt.y - cy) * (pt.y - cy)
            dSq <= innerRadiusSq 
        }
        
        for (i in 0 until 5) {
            val idx = innerPts[i]
            lensPts[idx] = Point(lensPts[idx].x + 50.0, lensPts[idx].y - 50.0) // Big outlier
        }
        
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, spacing)
        
        assertTrue(result.success)
        
        // Lambda should still be ~0.05 thanks to Huber IRLS
        assertEquals(0.05, result.lambda1, 0.01)
        
        // Optical field retained count should be total inner pts - 5 outliers
        val expectedRetained = innerPts.size - 5
        assertEquals(expectedRetained, result.opticalFieldRetainedCount)
    }
}
