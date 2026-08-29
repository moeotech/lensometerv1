import re

files = [
    'app/src/main/java/com/example/ui/ExperimentScreen.kt',
    'app/src/main/java/com/example/ui/FocusExperimentScreen.kt',
    'app/src/main/java/com/example/ui/LensExperimentScreen.kt'
]

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()

    if "var isDisposed = false" in content: continue

    # 1. Add var isDisposed = false right after DisposableEffect
    content = content.replace("    DisposableEffect(lifecycleOwner) {", "    DisposableEffect(lifecycleOwner) {\n        var isDisposed = false")

    # 2. Add isDisposed = true in onDispose
    content = content.replace("        onDispose {", "        onDispose {\n            isDisposed = true")

    # 3. Add Handler and postDelayed inside addListener
    pattern = r"                cameraProviderFuture\.addListener\(\{([\s\S]*?)\}, ContextCompat\.getMainExecutor\(context\)\)"
    
    def replacer(match):
        inner_code = match.group(1)
        # Indent inner_code
        indented = "\n".join(["    " + line if line.strip() else line for line in inner_code.split("\n")])
        new_block = """                cameraProviderFuture.addListener({
                    android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                        if (isDisposed) return@postDelayed
%s
                    }, 400)
                }, ContextCompat.getMainExecutor(context))""" % indented
        return new_block

    content = re.sub(pattern, replacer, content)

    with open(filepath, 'w') as f:
        f.write(content)

