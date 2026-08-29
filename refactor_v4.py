import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# I will parse and replace the body of analyzePoints from "val ptsToMeasureRef = matchedRef.toMutableList()" down to "val fieldFitRms = ..."

