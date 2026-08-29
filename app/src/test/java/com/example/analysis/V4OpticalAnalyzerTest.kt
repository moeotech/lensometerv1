package com.example.analysis

import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.opencv.core.Point
import org.opencv.android.OpenCVLoader
import kotlin.math.*

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
    fun testPureRotation() {
        val w = 1000.0
        val h = 1000.0
        val spacing = 30.0
        val refPts = generateGrid(w, h, spacing)
        
        val cx = w / 2.0
        val cy = h / 2.0
        
        val theta = Math.toRadians(5.0)
        val cosT = Math.cos(theta)
        val sinT = Math.sin(theta)
        
        val lensPts = mutableListOf<Point>()
        for (pt in refPts) {
            val dxC = pt.x - cx
            val dyC = pt.y - cy
            val rotX = cx + dxC * cosT - dyC * sinT
            val rotY = cy + dxC * sinT + dyC * cosT
            lensPts.add(Point(rotX, rotY))
        }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, spacing)
        
        assertTrue("Run should succeed", result.success)
        assertEquals(0.0, result.lambda1, 0.01)
        assertEquals(0.0, result.lambda2, 0.01)
        assertEquals(0.0, result.isotropic, 0.01)
        assertEquals(0.0, result.anisotropic, 0.01)
    }

    @Test
    fun testIsotropicScaling() {
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
                val scale = 1.05
                val scaledX = cx + (pt.x - cx) * scale
                val scaledY = cy + (pt.y - cy) * scale
                lensPts.add(Point(scaledX, scaledY))
            }
        }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, spacing)
        
        assertTrue("Run should succeed", result.success)
        assertEquals(0.05, result.lambda1, 0.01)
        assertEquals(0.05, result.lambda2, 0.01)
        assertEquals(0.0, result.anisotropic, 0.01)
    }

    @Test
    fun testAnisotropicScaling() {
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
                val scaleX = 1.08
                val scaleY = 0.98
                val scaledX = cx + (pt.x - cx) * scaleX
                val scaledY = cy + (pt.y - cy) * scaleY
                lensPts.add(Point(scaledX, scaledY))
            }
        }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, spacing)
        
        assertTrue("Run should succeed", result.success)
        assertEquals(0.08, result.lambda1, 0.01)
        assertEquals(-0.02, result.lambda2, 0.01)
        assertEquals(abs(result.lambda1 - result.lambda2), result.anisotropic, 0.001)
        assertEquals(0.1, result.anisotropic, 0.01)
    }

    @Test
    fun testRotationAndAnisotropicScaling() {
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
            
            // Apply camera rotation
            val dxC = pt.x - cx
            val dyC = pt.y - cy
            val rotX = cx + dxC * cosT - dyC * sinT
            val rotY = cy + dxC * sinT + dyC * cosT
            
            if (dSq > innerRadiusSq) {
                lensPts.add(Point(rotX, rotY))
            } else {
                // Apply anisotropic deformation first, then camera rotation? Or just apply directly on the rotated coords
                // If the lens distorts the image, then camera rotation happens later, but they are linear so they compose.
                // Let's model a lens with L1=0.08, L2=-0.02 along x/y axes:
                val u = pt.x + dxC * 0.08
                val v = pt.y + dyC * -0.02
                
                // Now rotate this distorted image
                val dxU = u - cx
                val dyV = v - cy
                val finalX = cx + dxU * cosT - dyV * sinT
                val finalY = cy + dxU * sinT + dyV * cosT
                lensPts.add(Point(finalX, finalY))
            }
        }
        
        val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, w, h, refPts.size, lensPts.size, spacing)
        
        assertTrue("Run should succeed", result.success)
        assertEquals(0.08, result.lambda1, 0.01)
        assertEquals(-0.02, result.lambda2, 0.01)
        assertEquals(0.1, result.anisotropic, 0.01)
    }
}
