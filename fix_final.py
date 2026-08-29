import re
with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    content = f.read()

# Remove any extra } before fun proxyToBitmap
content = re.sub(r'\}\s*\}\s*\}\s*\}\s*\}\s*\}\s*fun proxyToBitmap', '\nfun proxyToBitmap', content)

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.write(content)
