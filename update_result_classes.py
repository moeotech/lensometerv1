import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Replace V4RunResult globalScaleAmbiguous
pattern1 = r'val globalScaleAmbiguous: Boolean = false,'
replacement1 = """val registrationModel: String = "",
    val registrationRotationDeg: Double = 0.0,
    val registrationTx: Double = 0.0,
    val registrationTy: Double = 0.0,
    val registrationScale: Double = 0.0,"""

content = re.sub(pattern1, replacement1, content)

# But wait, there are two occurrences of globalScaleAmbiguous (V4RunResult and V4Result)
# The second one is at the end of V4Result without comma:
pattern2 = r'val globalScaleAmbiguous: Boolean = false\n\)'
replacement2 = """val registrationModel: String = "",
    val registrationRotationDeg: Double = 0.0,
    val registrationTx: Double = 0.0,
    val registrationTy: Double = 0.0,
    val registrationScale: Double = 0.0
)"""

content = re.sub(pattern2, replacement2, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
