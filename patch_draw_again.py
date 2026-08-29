import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

content = re.sub(r'fun drawVectorMap\(result: V4Result, mag: Float\): Bitmap\?',
                 r'fun drawVectorMap(result: V4Result, mag: Float, useCorrectedVectors: Boolean = true): Bitmap?', content)

content = re.sub(r'drawVectorMapInternal\(result\.lastRunResult, mag\)',
                 r'drawVectorMapInternal(result.lastRunResult, mag, useCorrectedVectors)', content)

content = re.sub(r'private fun drawVectorMapInternal\(run: V4RunResult, mag: Float\): Bitmap \{',
                 r'private fun drawVectorMapInternal(run: V4RunResult, mag: Float, useCorrectedVectors: Boolean = true): Bitmap {', content)

content = re.sub(r'val visualVectorMap = if \(lastRun\.referencePoints\.isNotEmpty\(\)\) \{\s*drawVectorMapInternal\(lastRun, 1f\)\s*\}',
                 r'val visualVectorMap = if (lastRun.referencePoints.isNotEmpty()) { drawVectorMapInternal(lastRun, 1f, true) }', content)


with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
