import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Replace data class V4RunResult
pattern = r"data class V4RunResult\(.*?\n\)"
replacement = """data class V4RunResult(
    val success: Boolean,
    val errorMessage: String = "",
    val axis: Double = 0.0,
    val lambda1: Double = 0.0,
    val lambda2: Double = 0.0,
    val isotropic: Double = 0.0,
    val anisotropic: Double = 0.0,
    val trackedDots: Int = 0,
    
    val topologyMatchCount: Int = 0,
    val registrationFeatureCount: Int = 0,
    val registrationInliers: Int = 0,
    val registrationRms: Double = 0.0,
    
    val opticalFieldInputCount: Int = 0,
    val opticalFieldRetainedCount: Int = 0,
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
    val candidateMatches: Int = 0,
    val acceptedMatches: Int = 0,
    val matchRejections: Map<String, Int> = emptyMap(),
    val spatialCoveragePct: Double = 0.0,
    val quadrantCoverage: Int = 0,
    val matrixRank: Int = 0,
    val conditionNumber: Double = 0.0,
    val degeneracyStatus: String = "",
    val framesCaptured: Int = 0,
    val framesAccepted: Int = 0,
    val framesRejected: Int = 0,
    val temporalTrackCount: Int = 0,
    val stableTrackCount: Int = 0,
    val medianTrackLifetime: Double = 0.0,
    val rejectedReferencePoints: List<Point> = emptyList(),
    val unmatchedLensPoints: List<Point> = emptyList()
)"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
