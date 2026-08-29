import re

files = [
    'app/src/main/java/com/example/ui/ExperimentScreen.kt',
    'app/src/main/java/com/example/ui/FocusExperimentScreen.kt',
    'app/src/main/java/com/example/ui/LensExperimentScreen.kt'
]

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Remove the observer wrapper
    content = content.replace("        val observer = androidx.lifecycle.LifecycleEventObserver { _, event ->\n            if (event == androidx.lifecycle.Lifecycle.Event.ON_RESUME) {", "")
    
    # 2. Replace the end of the ON_RESUME block and the whole ON_PAUSE block
    # We need to find the matching brackets. Let's use regex for the specific pattern.
    pattern_pause = r"                    } catch \(exc: Exception\) \{\}\n                \}, ContextCompat\.getMainExecutor\(context\)\)\n            \} else if \(event == androidx\.lifecycle\.Lifecycle\.Event\.ON_PAUSE\) \{\n(?:.|\n)*?            \}\n        \}\n\s*lifecycle\.addObserver\(observer\)\n"
    
    # In some files it might be slightly different. Let's look at LensExperimentScreen
    match = re.search(pattern_pause, content)
    if match:
        content = re.sub(pattern_pause, r"                    } catch (exc: Exception) {}\n                }, ContextCompat.getMainExecutor(context))\n", content)
    
    # 3. Remove lifecycle.removeObserver(observer) from onDispose
    content = content.replace("            lifecycle.removeObserver(observer)\n", "")

    with open(filepath, 'w') as f:
        f.write(content)
