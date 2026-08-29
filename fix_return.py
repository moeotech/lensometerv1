import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r'globalScaleAmbiguous = globalScaleAmbiguous,'
replacement = r"""registrationModel = if (useRigidFallback) "RIGID_FALLBACK" else "RIGID_ANCHOR",
                registrationRotationDeg = 0.0, // To be filled later
                registrationTx = 0.0,
                registrationTy = 0.0,
                registrationScale = 1.0,"""

content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
