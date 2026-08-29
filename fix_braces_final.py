import re
with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    content = f.read()

# Replace any sequence of } before fun proxyToBitmap
content = re.sub(r'\}*\s*fun proxyToBitmap', '}}}}}fun proxyToBitmap', content)

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.write(content)
