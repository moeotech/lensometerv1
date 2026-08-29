with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Add lastRunResult to V4Result
content = content.replace(
    "val visualVectorMap: Bitmap? = null",
    "val visualVectorMap: Bitmap? = null,\n    val lastRunResult: V4RunResult? = null"
)

# Pass lastRun to V4Result
content = content.replace(
    "lambda2 = lastRun.lambda2,\n            visualVectorMap = visualVectorMap",
    "lambda2 = lastRun.lambda2,\n            visualVectorMap = visualVectorMap,\n            lastRunResult = lastRun"
)

# Update drawVectorMap
old_draw = """    fun drawVectorMap(result: Bitmap, mag: Float): Bitmap {
        // We will just redraw it here since we can't easily scale the vectors on an already drawn bitmap
        // In a real app we'd save the points and redraw them.
        // For simplicity we'll just return the original for now, but a proper implementation would re-render.
        return result 
    }"""
new_draw = """    fun drawVectorMap(result: V4Result, mag: Float): Bitmap? {
        if (result.lastRunResult == null) return null
        return drawVectorMapInternal(result.lastRunResult, mag)
    }"""
content = content.replace(old_draw, new_draw)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
