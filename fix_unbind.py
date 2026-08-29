import re

files = [
    'app/src/main/java/com/example/ui/ExperimentScreen.kt',
    'app/src/main/java/com/example/ui/FocusExperimentScreen.kt',
    'app/src/main/java/com/example/ui/LensExperimentScreen.kt'
]

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace specific unbind with unbindAll
    content = content.replace("previewRef?.let { provider.unbind(it) }; imageAnalysisRef?.let { provider.unbind(it) }", "provider.unbindAll()")

    with open(filepath, 'w') as f:
        f.write(content)
