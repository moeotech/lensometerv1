import os
import re

directory = 'app/src/main/java/com/example/ui/'
for filename in os.listdir(directory):
    if filename.endswith("Screen.kt"):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            content = f.read()
            
        content = re.sub(r'if \(previewRef != null\) provider\.unbind\(previewRef\)', 'provider.unbindAll()', content)
        content = re.sub(r'if \(imageAnalysisRef != null\) provider\.unbind\(imageAnalysisRef\)', '', content)
        
        with open(filepath, 'w') as f:
            f.write(content)
