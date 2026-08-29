import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r'opticalRejectedObservedPoints = opticalPairs\.filter \{ it\.status != "RETAINED" \}\.map \{ it\.observed \},'
replacement = r"""opticalRejectedObservedPoints = opticalPairs.filter { it.status != "RETAINED" }.map { it.observed },
                dispMedian = dispMedian,
                dispMAD = dispMAD,
                dispP90 = dispP90,
                dispMax = dispMax,
                pairs = opticalPairs,"""

content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
