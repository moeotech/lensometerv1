import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r'val dx = \(lensPt.x - refPt.x\) \* mag\n\s*val dy = \(lensPt.y - refPt.y\) \* mag'
replacement = r"""val dx = if (useCorrectedVectors) pair.correctedDisplacement.x * mag else pair.displacement.x * mag
            val dy = if (useCorrectedVectors) pair.correctedDisplacement.y * mag else pair.displacement.y * mag"""

content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
