import os
import re

directory = 'app/src/main/java/com/example/ui/'
for filename in os.listdir(directory):
    if filename.endswith("Screen.kt"):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as f:
            content = f.read()
            
        # We want to replace:
        # android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
        #     if (isDisposed) return@postDelayed
        #     ... code ...
        # }, 1000)
        # with:
        # if (!isDisposed) {
        #     ... code ...
        # }
        
        # It's a bit tricky to do with regex because of nested blocks.
        # Let's see if we can do it with a simple replacement.
