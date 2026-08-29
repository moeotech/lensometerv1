import re
import os

files = [
    'app/src/main/java/com/example/ui/LensExperimentScreen.kt',
    'app/src/main/java/com/example/ui/ExperimentScreen.kt',
    'app/src/main/java/com/example/ui/FocusExperimentScreen.kt',
    'app/src/main/java/com/example/ui/V4ExperimentScreen.kt'
]

replacement = """                imageAnalysisRef?.clearAnalyzer()
                if (previewRef != null) provider.unbind(previewRef)
                if (imageAnalysisRef != null) provider.unbind(imageAnalysisRef)
"""

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace the block
    content = re.sub(r'imageAnalysisRef\?\.clearAnalyzer\(\)\s*// provider\.unbindAll\(\).*?\n', replacement, content)
    
    with open(filepath, 'w') as f:
        f.write(content)

print("done")
