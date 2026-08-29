import re

def fix_screen(filepath, has_camera2):
    with open(filepath, 'r') as f:
        content = f.read()

    # Move state and effect down to after cameraControlRef declaration
    state_and_effect = """
    var flashMode by remember { mutableStateOf("AUTO") }
    LaunchedEffect(flashMode, cameraControlRef) {
        try {
            when (flashMode) {
                "ON" -> cameraControlRef?.enableTorch(true)
                "OFF" -> cameraControlRef?.enableTorch(false)
                "AUTO" -> {
                    cameraControlRef?.enableTorch(false)"""
    if has_camera2:
        state_and_effect += """
                    camera2ControlRef?.let { c2c ->
                        val builder = CaptureRequestOptions.Builder()
                        builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON_AUTO_FLASH)
                        c2c.captureRequestOptions = builder.build()
                    }"""
    state_and_effect += """
                }
            }
        } catch (e: Exception) {}
    }
"""

    # First remove the one we just added at the top
    content = re.sub(r'\n\s*var flashMode by remember.*?catch \(e: Exception\) \{\}\n\s*\}\n', '', content, flags=re.DOTALL)
    
    # Now find where cameraControlRef is defined and add it there
    if has_camera2:
        content = content.replace("var camera2ControlRef by remember { mutableStateOf<Camera2CameraControl?>(null) }", "var camera2ControlRef by remember { mutableStateOf<Camera2CameraControl?>(null) }\n" + state_and_effect)
    else:
        content = content.replace("var cameraControlRef by remember { mutableStateOf<CameraControl?>(null) }", "var cameraControlRef by remember { mutableStateOf<CameraControl?>(null) }\n" + state_and_effect)

    with open(filepath, 'w') as f:
        f.write(content)

fix_screen('app/src/main/java/com/example/ui/ExperimentScreen.kt', has_camera2=False)
fix_screen('app/src/main/java/com/example/ui/FocusExperimentScreen.kt', has_camera2=True)
