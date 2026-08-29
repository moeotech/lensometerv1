import re

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    content = f.read()

# 1. Add flashMode state
content = content.replace("    var imgH by remember { mutableIntStateOf(1) }", 
                          "    var imgH by remember { mutableIntStateOf(1) }\n    var flashMode by remember { mutableStateOf(\"AUTO\") }")

# 2. Add LaunchedEffect for flash mode
effect_code = """
    LaunchedEffect(flashMode, cameraControlRef) {
        try {
            when (flashMode) {
                "ON" -> cameraControlRef?.enableTorch(true)
                "OFF" -> cameraControlRef?.enableTorch(false)
                "AUTO" -> {
                    cameraControlRef?.enableTorch(false)
                    camera2ControlRef?.let { c2c ->
                        val builder = CaptureRequestOptions.Builder()
                        builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON_AUTO_FLASH)
                        c2c.captureRequestOptions = builder.build()
                    }
                }
            }
        } catch (e: Exception) {}
    }

    LaunchedEffect(isStable, phase)"""
content = content.replace("    LaunchedEffect(isStable, phase)", effect_code, 1)

# 3. UI toggle inside the Box
ui_toggle_code = """            Canvas(modifier = Modifier.fillMaxSize()) {"""
ui_toggle_replacement = """            Canvas(modifier = Modifier.fillMaxSize()) {
                val cx = size.width / 2
                val cy = size.height / 2
                
                // Fixed Crosshair
                drawLine(Color.Red, Offset(cx - 20, cy), Offset(cx + 20, cy), 4f)
                drawLine(Color.Red, Offset(cx, cy - 20), Offset(cx, cy + 20), 4f)
"""
content = content.replace(ui_toggle_code, ui_toggle_replacement)

# Remove old red crosshair
content = content.replace("                    drawLine(Color.Red, Offset(cx - 20, cy), Offset(cx + 20, cy), 2f)\n                    drawLine(Color.Red, Offset(cx, cy - 20), Offset(cx, cy + 20), 2f)", "")

# Remove white moving crosshair
content = content.replace("                            drawLine(Color.White, Offset(-15f, 0f), Offset(15f, 0f), 4f)\n                            drawLine(Color.White, Offset(0f, -15f), Offset(0f, 15f), 4f)", "")

# Add segmented control before Canvas
canvas_tag = """            Canvas(modifier = Modifier.fillMaxSize()) {"""
segmented_control = """
            Row(
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
content = content.replace(canvas_tag, segmented_control, 1)

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.write(content)
