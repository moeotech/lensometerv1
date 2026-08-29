import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# 1. Update V4RunResult with new fields
v4run_pattern = r'val rejectedReferencePoints: List<Point> = emptyList\(\),\n\s*val unmatchedLensPoints: List<Point> = emptyList\(\)\n\)'
v4run_replacement = r"""val rejectedReferencePoints: List<Point> = emptyList(),
    val unmatchedLensPoints: List<Point> = emptyList(),
    val localOutlierRejections: Int = 0,
    val crossingVectorRejections: Int = 0,
    val medianLocalResidual: Double = 0.0,
    val madLocalResidual: Double = 0.0,
    val opticalRejectedReferencePoints: List<Point> = emptyList(),
    val opticalRejectedObservedPoints: List<Point> = emptyList()
)"""

content = re.sub(v4run_pattern, v4run_replacement, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
