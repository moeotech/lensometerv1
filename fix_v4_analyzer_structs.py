with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

import re

# Update V4Result
result_repl = """data class V4Result(
    val success: Boolean,
    val errorMessage: String = "",
    val sphDisplay: String = "NOT CALIBRATED",
    val cylDisplay: String = "NOT CALIBRATED",
    val axisDisplay: String = "",
    val lambda1: Double = 0.0,
    val lambda2: Double = 0.0,
    val isotropic: Double = 0.0,
    val anisotropic: Double = 0.0,
    val lambda1Std: Double = 0.0,
    val lambda2Std: Double = 0.0,
    val isotropicStd: Double = 0.0,
    val anisotropicStd: Double = 0.0,
    val allRuns: List<V4RunResult> = emptyList(),
    val trackedDots: Int = 0,
    val registrationRms: Double = 0.0,
    val ransacInliers: Int = 0,
    val fieldFitRms: Double = 0.0,
    val refDotCount: Int = 0,
    val lensDotCount: Int = 0,
    val meanDx: Double = 0.0,
    val meanDy: Double = 0.0,
    val visualVectorMap: Bitmap? = null,
    val lastRunResult: V4RunResult? = null,
    val globalScaleAmbiguous: Boolean = false
)"""
content = re.sub(r'data class V4Result\([\s\S]*?\)', result_repl, content, count=1)

# Update V4RunResult
run_repl = """data class V4RunResult(
    val success: Boolean,
    val errorMessage: String = "",
    val axis: Double = 0.0,
    val lambda1: Double = 0.0,
    val lambda2: Double = 0.0,
    val isotropic: Double = 0.0,
    val anisotropic: Double = 0.0,
    val trackedDots: Int = 0,
    val registrationRms: Double = 0.0,
    val ransacInliers: Int = 0,
    val fieldFitRms: Double = 0.0,
    val refDotCount: Int = 0,
    val lensDotCount: Int = 0,
    val meanDx: Double = 0.0,
    val meanDy: Double = 0.0,
    val referencePoints: List<Point> = emptyList(),
    val observedPoints: List<Point> = emptyList(),
    val refWidth: Int = 0,
    val refHeight: Int = 0,
    val globalScaleAmbiguous: Boolean = false,
    val framesCaptured: Int = 0,
    val framesAccepted: Int = 0,
    val framesRejected: Int = 0
)"""
content = re.sub(r'data class V4RunResult\([\s\S]*?\)', run_repl, content, count=1)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
