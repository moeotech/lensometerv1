import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r'dispMax = dispMax,\n\s*pairs = opticalPairs,'
replacement = r"""dispMax = dispMax,
                pairs = opticalPairs,
                globalMotionX = globalMotionX,
                globalMotionY = globalMotionY,
                globalMotionMagnitude = globalMotionMagnitude,
                correctedDispMedian = correctedDispMedian,
                correctedDispMAD = correctedDispMAD,
                correctedDispP90 = correctedDispP90,
                correctedDispMax = correctedDispMax,"""

content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
