import re

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'r') as f:
    content = f.read()

# Replace all instance creations with object calls
content = re.sub(
    r'val analyzer = V4OpticalAnalyzer\(spacing = 30\.0, center = Point\([^)]+\)\)\n\s*val ([a-zA-Z]+)Result = analyzer\.analyzePoints\(refPts, ([a-zA-Z]+LensPts), 800, 600, useRigidFallback = true\)',
    r'val \1Result = V4OpticalAnalyzer.analyzePoints(refPts, \2, 800.0, 600.0, refPts.size, \2.size, 30.0, useRigidFallback = true)',
    content
)

content = re.sub(
    r'val analyzer = V4OpticalAnalyzer\(spacing = 30\.0, center = Point\([^)]+\)\)\n\s*val result = analyzer\.analyzePoints\(refPts, lensPts, 800, 600, useRigidFallback = true\)',
    r'val result = V4OpticalAnalyzer.analyzePoints(refPts, lensPts, 800.0, 600.0, refPts.size, lensPts.size, 30.0, useRigidFallback = true)',
    content
)

with open('app/src/test/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'w') as f:
    f.write(content)
