import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

res_old = """    val anisotropicStd: Double = 0.0,
    val allRuns: List<V4RunResult> = emptyList(),
    val trackedDots: Int = 0,
    val registrationRms: Double = 0.0,
    val ransacInliers: Int = 0,
    val fieldFitRms: Double = 0.0,"""

res_new = """    val anisotropicStd: Double = 0.0,
    val allRuns: List<V4RunResult> = emptyList(),
    val trackedDots: Int = 0,
    val registrationRms: Double = 0.0,
    val registrationInliers: Int = 0,
    val fieldFitRms: Double = 0.0,"""

content = content.replace(res_old, res_new)
content = content.replace("ransacInliers = lastRun.ransacInliers,", "registrationInliers = lastRun.registrationInliers,")

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)

