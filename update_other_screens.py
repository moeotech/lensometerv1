import re
import os

def process_file(filepath, has_camera2=True):
    if not os.path.exists(filepath): return
    with open(filepath, 'r') as f:
        content = f.read()

    # Skip if already has flashMode
    if "flashMode" in content: return

    # Add flashMode state
    if has_camera2:
        content = content.replace("var progress by remember", "var flashMode by remember { mutableStateOf(\"AUTO\") }\n    var progress by remember")
    else:
        content = content.replace("var progress by remember", "var flashMode by remember { mutableStateOf(\"AUTO\") }\n    var progress by remember")

    if "var flashMode" not in content:
        content = content.replace("var isStable by remember", "var flashMode by remember { mutableStateOf(\"AUTO\") }\n    var isStable by remember")

    # Add LaunchedEffect
    effect_code = """
    LaunchedEffect(flashMode, cameraControlRef) {
        try {
            when (flashMode) {
                "ON" -> cameraControlRef?.enableTorch(true)
                "OFF" -> cameraControlRef?.enableTorch(false)
                "AUTO" -> {
                    cameraControlRef?.enableTorch(false)
"""
    if has_camera2:
        effect_code += """                    camera2ControlRef?.let { c2c ->
                        val builder = CaptureRequestOptions.Builder()
                        builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON_AUTO_FLASH)
                        c2c.captureRequestOptions = builder.build()
                    }
"""
    effect_code += """                }
            }
        } catch (e: Exception) {}
    }

    LaunchedEffect"""

    content = content.replace("    LaunchedEffect", effect_code, 1)

    # UI toggle inside Box
    ui_toggle_replacement = """            Row(
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .padding(top = 16.dp)
                    .background(Color(0x88000000), RoundedCornerShape(8.dp)),
                horizontalArrangement = Arrangement.Center
            ) {
                TextButton(onClick = { flashMode = "AUTO" }) {
                    Text("AUTO", color = if (flashMode == "AUTO") Color.Yellow else Color.White)
                }
                TextButton(onClick = { flashMode = "ON" }) {
                    Text("ON", color = if (flashMode == "ON") Color.Yellow else Color.White)
                }
                TextButton(onClick = { flashMode = "OFF" }) {
                    Text("OFF", color = if (flashMode == "OFF") Color.Yellow else Color.White)
                }
            }

            Canvas(modifier = Modifier.fillMaxSize()) {"""
            
    content = content.replace("            Canvas(modifier = Modifier.fillMaxSize()) {", ui_toggle_replacement)

    with open(filepath, 'w') as f:
        f.write(content)

process_file('app/src/main/java/com/example/ui/ExperimentScreen.kt', has_camera2=False)
process_file('app/src/main/java/com/example/ui/FocusExperimentScreen.kt', has_camera2=True)
