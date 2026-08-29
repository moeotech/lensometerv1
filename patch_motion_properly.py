import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r'val retainedPairs = opticalPairs\.filter \{ it\.status == "RETAINED" \}'
replacement = r"""val retainedPairs = opticalPairs.filter { it.status == "RETAINED" }
            
            // Motion correction
            val dxs = retainedPairs.map { it.displacement.x }.sorted()
            val dys = retainedPairs.map { it.displacement.y }.sorted()
            val globalMotionX = if (dxs.isNotEmpty()) dxs[dxs.size / 2] else 0.0
            val globalMotionY = if (dys.isNotEmpty()) dys[dys.size / 2] else 0.0
            val globalMotionMagnitude = kotlin.math.hypot(globalMotionX, globalMotionY)
            
            for (pair in retainedPairs) {
                pair.correctedDisplacement = Point(pair.displacement.x - globalMotionX, pair.displacement.y - globalMotionY)
            }
            
            val correctedMags = retainedPairs.map { kotlin.math.hypot(it.correctedDisplacement.x, it.correctedDisplacement.y) }.sorted()
            var correctedDispMedian = 0.0
            var correctedDispMAD = 0.0
            var correctedDispP90 = 0.0
            var correctedDispMax = 0.0
            if (correctedMags.isNotEmpty()) {
                correctedDispMedian = correctedMags[correctedMags.size / 2]
                correctedDispMAD = correctedMags.map { kotlin.math.abs(it - correctedDispMedian) }.sorted()[correctedMags.size / 2]
                correctedDispP90 = correctedMags[(correctedMags.size * 0.9).toInt().coerceAtMost(correctedMags.size - 1)]
                correctedDispMax = correctedMags.last()
            }"""

content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
