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

    LaunchedEffect"""
content = content.replace("    LaunchedEffect", effect_code, 1)

# 3. Add UI toggle inside the Box
ui_toggle_code = """
            Canvas(modifier = Modifier.fillMaxSize()) {
"""
ui_toggle_replacement = """
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

            Canvas(modifier = Modifier.fillMaxSize()) {
"""
content = content.replace(ui_toggle_code, ui_toggle_replacement)

# 4. Move crosshair logic
content = content.replace("                    drawLine(Color.Red, Offset(cx - 20, cy), Offset(cx + 20, cy), 2f)\n                    drawLine(Color.Red, Offset(cx, cy - 20), Offset(cx, cy + 20), 2f)", "")
content = content.replace("                            drawLine(Color.White, Offset(-15f, 0f), Offset(15f, 0f), 4f)\n                            drawLine(Color.White, Offset(0f, -15f), Offset(0f, 15f), 4f)", "")

canvas_end_code = """
                }
            }
"""
canvas_end_replacement = """
                }
                drawLine(Color.Red, Offset(cx - 20, cy), Offset(cx + 20, cy), 4f)
                drawLine(Color.Red, Offset(cx, cy - 20), Offset(cx, cy + 20), 4f)
            }
"""
content = content.replace(canvas_end_code, canvas_end_replacement, 1)

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.write(content)
