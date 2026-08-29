import re
with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

data_class_replacement = """data class V4RunResult(
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
    val framesRejected: Int = 0,
    val candidateMatches: Int = 0,
    val acceptedMatches: Int = 0,
    val rejectedMatches: Int = 0,
    val matrixRank: Int = 0,
    val conditionNumber: Double = 0.0,
    val degeneracyStatus: String = "OK"
)"""
content = re.sub(r'data class V4RunResult\([\s\S]*?\n\)', data_class_replacement, content)
with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
