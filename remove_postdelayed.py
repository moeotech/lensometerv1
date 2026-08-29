import os
import re

directory = 'app/src/main/java/com/example/ui/'
for filename in os.listdir(directory):
    if filename.endswith("Screen.kt"):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            content = f.read()
            
        # We need to replace:
        # android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
        #     if (isDisposed) return@postDelayed
        # with:
        # if (isDisposed) return@addListener
        
        # Then we need to remove the closing `}, 1000)` and replace with `}`.
        
        pattern = r'android\.os\.Handler\(android\.os\.Looper\.getMainLooper\(\)\)\.postDelayed\(\{[\s\n]*if\s*\(isDisposed\)\s*return@postDelayed'
        replacement = r'if (isDisposed) return@addListener'
        
        content = re.sub(pattern, replacement, content)
        
        # Also fix the closing block
        content = re.sub(r'\}, 1000\)', '', content)
        
        with open(filepath, 'w') as f:
            f.write(content)
