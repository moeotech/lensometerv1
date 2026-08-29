import re

def fix(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # For ExperimentScreen.kt
    content = content.replace("    }\n    } catch (e: Exception) {}\n    }", "")
    content = content.replace("    } catch (e: Exception) {}\n    }\n\n    LaunchedEffect(Unit)", "    LaunchedEffect(Unit)")

    # For FocusExperimentScreen.kt
    content = content.replace("    }\n        } catch (e: Exception) {}\n    }\n\n    LaunchedEffect(Unit)", "    LaunchedEffect(Unit)")

    with open(filepath, 'w') as f:
        f.write(content)

fix('app/src/main/java/com/example/ui/ExperimentScreen.kt')
fix('app/src/main/java/com/example/ui/FocusExperimentScreen.kt')
