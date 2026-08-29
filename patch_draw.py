import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern1 = r'fun drawVectorMap\(result: V4Result, mag: Float\): Bitmap\? \{'
replacement1 = r'fun drawVectorMap(result: V4Result, mag: Float, useCorrectedVectors: Boolean = true): Bitmap? {'
content = content.replace(pattern1, replacement1)

pattern2 = r'return drawVectorMapInternal\(result.lastRunResult, mag\)'
replacement2 = r'return drawVectorMapInternal(result.lastRunResult, mag, useCorrectedVectors)'
content = content.replace(pattern2, replacement2)

pattern3 = r'private fun drawVectorMapInternal\(run: V4RunResult, mag: Float\): Bitmap \{'
replacement3 = r'private fun drawVectorMapInternal(run: V4RunResult, mag: Float, useCorrectedVectors: Boolean = true): Bitmap {'
content = content.replace(pattern3, replacement3)

pattern4 = r'drawVectorMapInternal\(lastRun, 1f\)'
replacement4 = r'drawVectorMapInternal(lastRun, 1f, true)'
content = content.replace(pattern4, replacement4)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
