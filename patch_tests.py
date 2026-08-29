import os
path = "app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt"
with open(path, "r") as f:
    text = f.read()

replacement = """
    // --- SYNTHETIC TESTS FOR TOPOLOGY AND MATCHING ---

    private fun drawDots(points: List<Point>, w: Int, h: Int): Bitmap {
        val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        bitmap.eraseColor(android.graphics.Color.WHITE)
        val canvas = android.graphics.Canvas(bitmap)
        val paint = android.graphics.Paint().apply {
            color = android.graphics.Color.BLACK
            style = android.graphics.Paint.Style.FILL
            isAntiAlias = true
        }
        for (p in points) {
            canvas.drawCircle(p.x.toFloat(), p.y.toFloat(), 3.0f, paint)
        }
        return bitmap
    }

    @Test
    fun testAC_matching_perfectGrid() = kotlinx.coroutines.runBlocking {
        val w = 600; val h = 600
        val refPts = generateGrid(w.toDouble(), h.toDouble(), 40.0)
        
        val refBmp = drawDots(refPts, w, h)
        val lensBmp = drawDots(refPts, w, h)
        
        val analyzer = V4OpticalAnalyzer
        val result = analyzer.analyze(List(5) { refBmp }, List(15) { lensBmp })
        
        assertTrue(result.success)
        assertTrue(result.acceptedMatches > refPts.size * 0.8)
        assertEquals(0, result.matchRejections["gridCollisions"] ?: 0)
    }

    @Test
    fun testAD_matching_translatedGrid() = kotlinx.coroutines.runBlocking {
        val w = 600; val h = 600
        val refPts = generateGrid(w.toDouble(), h.toDouble(), 40.0)
        
        val lensPts = refPts.map { Point(it.x + 12.0, it.y - 8.0) }
        
        val refBmp = drawDots(refPts, w, h)
        val lensBmp = drawDots(lensPts, w, h)
        
        val analyzer = V4OpticalAnalyzer
        val result = analyzer.analyze(List(5) { refBmp }, List(15) { lensBmp })
        
        assertTrue(result.success)
        assertTrue(result.acceptedMatches > refPts.size * 0.8)
    }
    
    @Test
    fun testAE_matching_radialDistortion() = kotlinx.coroutines.runBlocking {
        val w = 600; val h = 600
        val refPts = generateGrid(w.toDouble(), h.toDouble(), 40.0)
        
        val k = -0.02
        val lensPts = refPts.map { 
            val cx = it.x - w/2.0
            val cy = it.y - h/2.0
            Point(it.x + cx * k, it.y + cy * k) 
        }
        
        val refBmp = drawDots(refPts, w, h)
        val lensBmp = drawDots(lensPts, w, h)
        
        val analyzer = V4OpticalAnalyzer
        val result = analyzer.analyze(List(5) { refBmp }, List(15) { lensBmp })
        
        assertTrue(result.success)
        assertTrue(result.acceptedMatches > refPts.size * 0.8)
    }
    
    @Test
    fun testAF_matching_missingAndFalseDots() = kotlinx.coroutines.runBlocking {
        val w = 600; val h = 600
        val refPts = generateGrid(w.toDouble(), h.toDouble(), 40.0)
        
        val k = -0.015
        val lensPts = refPts.mapIndexedNotNull { index, pt ->
            // Missing 20%
            if (index % 5 == 0) null
            else {
                val cx = pt.x - w/2.0
                val cy = pt.y - h/2.0
                Point(pt.x + cx * k, pt.y + cy * k) 
            }
        }.toMutableList()
        
        // Add 10% false dots
        for (i in 0 until (refPts.size * 0.1).toInt()) {
            lensPts.add(Point(Math.random() * w, Math.random() * h))
        }
        
        val refBmp = drawDots(refPts, w, h)
        val lensBmp = drawDots(lensPts, w, h)
        
        val analyzer = V4OpticalAnalyzer
        val result = analyzer.analyze(List(5) { refBmp }, List(15) { lensBmp })
        
        // As long as we get > 20 matches, it should pass
        assertTrue(result.success)
        assertTrue(result.acceptedMatches >= 20)
    }

}
"""

end_str = "}"
start_idx = text.rfind(end_str)

text = text[:start_idx] + replacement

with open(path, "w") as f:
    f.write(text)
