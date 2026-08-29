import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

optical_pair_old = """data class OpticalPair(
    val reference: Point,
    val observed: Point,
    val displacement: Point,
    val originalIndex: Int,
    var status: String = "RETAINED"
)"""
optical_pair_new = """data class OpticalPair(
    val reference: Point,
    val observed: Point,
    val displacement: Point,
    val originalIndex: Int,
    var status: String = "RETAINED",
    var correctedDisplacement: Point = Point(0.0, 0.0)
)"""
content = content.replace(optical_pair_old, optical_pair_new)

v4runresult_old = """    val dispMax: Double = 0.0,
    val pairs: List<OpticalPair> = emptyList()
)"""
v4runresult_new = """    val dispMax: Double = 0.0,
    val pairs: List<OpticalPair> = emptyList(),
    val globalMotionX: Double = 0.0,
    val globalMotionY: Double = 0.0,
    val globalMotionMagnitude: Double = 0.0,
    val correctedDispMedian: Double = 0.0,
    val correctedDispMAD: Double = 0.0,
    val correctedDispP90: Double = 0.0,
    val correctedDispMax: Double = 0.0
)"""
content = content.replace(v4runresult_old, v4runresult_new)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
