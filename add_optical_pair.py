import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

new_classes = """
data class OpticalPair(
    val reference: Point,
    val observed: Point,
    val displacement: Point,
    val originalIndex: Int,
    var status: String = "RETAINED"
)

data class V4RunResult(
"""
content = re.sub(r'data class V4RunResult\(', new_classes, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
