package com.example.analysis

import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.opencv.core.Point
import kotlin.math.*

@RunWith(RobolectricTestRunner::class)
@Config(manifest=Config.NONE)
class V4OpticalAnalyzerTest {

    init {
        nu.pattern.OpenCV.loadShared()
    }

    @Test
    fun testSyntheticDeformation() = runBlocking {
        val w = 640.0
        val h = 480.0
        
        val cx = w / 2.0
        val cy = h / 2.0
        
        // Target properties
        val isotropicScale = 1.05
        val anisotropicScale = 0.02
        val principalAxisRad = Math.PI / 6.0 // 30 degrees
        
        // Simulating some camera motion
        val camTx = 5.0
        val camTy = -3.0
        
        val matchedRef = mutableListOf<Point>()
        val matchedLens = mutableListOf<Point>()
        
        for (i in 0 until 10) {
            for (j in 0 until 10) {
                val x = 100.0 + i * 45.0
                val y = 50.0 + j * 40.0
                
                matchedRef.add(Point(x, y))
                
                val dx = x - cx
                val dy = y - cy
                val rSq = dx*dx + dy*dy
                val maxRSq = (min(w, h)/2.0) * (min(w, h)/2.0)
                
                var newX = x + camTx
                var newY = y + camTy
                
                // Only apply optical distortion if inside measurement zone (radius 0.7)
                if (rSq <= maxRSq * 0.49) {
                    val s00 = isotropicScale + anisotropicScale * cos(2 * principalAxisRad)
                    val s11 = isotropicScale - anisotropicScale * cos(2 * principalAxisRad)
                    val s01 = anisotropicScale * sin(2 * principalAxisRad)
                    
                    val u = s00 * dx + s01 * dy
                    val v = s01 * dx + s11 * dy
                    
                    newX = cx + u + camTx
                    newY = cy + v + camTy
                }
                
                matchedLens.add(Point(newX, newY))
            }
        }
        
        val result = V4OpticalAnalyzer.analyzePoints(matchedRef, matchedLens, w, h)
        
        assertTrue(result.success)
        
        val expectedIso = isotropicScale - 1.0
        val expectedAniso = anisotropicScale * 2.0
        
        assertEquals(expectedIso, result.isotropic, 0.005)
        assertEquals(expectedAniso, result.anisotropic, 0.005)
        
        val expectedAxis = (principalAxisRad * 180.0 / Math.PI)
        var err = abs(result.axis - expectedAxis) % 180.0
        if (err > 90) err = 180 - err
        assertEquals(0.0, err, 5.0)
    }
}
