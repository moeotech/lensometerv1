import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Modify point matching (increase distance threshold for direct lens)
content = content.replace("dist < 100.0", "dist < 200.0")

# Modify minimum points required
content = content.replace("if (matchedRef.size < 30)", "if (matchedRef.size < 10)")
content = content.replace("Matched dots < 30", "Matched dots < 10")

# Update analyzePoints call
analyze_call_old = """val res = analyzePoints(matchedRef, matchedLens, w, h)"""
analyze_call_new = """val res = analyzePoints(matchedRef, matchedLens, w, h, baseRefPoints.size, baseLensPoints.size)"""
content = content.replace(analyze_call_old, analyze_call_new)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
