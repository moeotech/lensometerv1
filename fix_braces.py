with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    content = f.read()

# fix runCaptureSequence
content = content.replace("            }\n\n    fun restoreAuto", "            }\n        }\n\n    fun restoreAuto")

# fix restoreAuto
content = content.replace("            c2c.captureRequestOptions = builder.build()\n\n    LaunchedEffect", "            c2c.captureRequestOptions = builder.build()\n        }\n    }\n\n    LaunchedEffect")

# fix LaunchedEffect
content = content.replace("            phase = LensExperimentPhase.RESULTS\n\n    Box", "            phase = LensExperimentPhase.RESULTS\n        }\n    }\n\n    Box")

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.write(content)
