import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Just extract up to the first instance of 'object V4OpticalAnalyzer'
idx = content.find("suspend fun analyze(")
if idx != -1:
    idx2 = content.find("suspend fun analyze(", idx + 10)
    if idx2 != -1:
        print("Found second analyze at", idx2)
        # we have duplicates!
