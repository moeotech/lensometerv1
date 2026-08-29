import re

def fix_screen(filepath, has_camera2):
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Clean up old broken insertions
    content = re.sub(r'var flashMode.*?AUTO"\)\s*\}\n\s*', '', content)
    content = re.sub(r'LaunchedEffect\(flashMode, cameraControlRef\).*?\}\s*\}\s*', '', content, flags=re.DOTALL)
    
    # Also clean up the inserted UI toggle if it's there
    content = re.sub(r'Row\(\s*modifier = Modifier\s*\.align\(Alignment\.TopCenter\).*?Text\("OFF".*?\}\s*\}\s*\}\s*Canvas\(modifier = Modifier\.fillMaxSize\(\)\) \{', 'Canvas(modifier = Modifier.fillMaxSize()) {', content, flags=re.DOTALL)

    # 2. Add state and effect right after `val lifecycleOwner = LocalLifecycleOwner.current`
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
    content = content.replace("val lifecycleOwner = LocalLifecycleOwner.current", "val lifecycleOwner = LocalLifecycleOwner.current\n" + state_and_effect)
    content = content.replace("val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current", "val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current\n" + state_and_effect)

    # 3. Add UI toggle
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
            
    content = content.replace("            Canvas(modifier = Modifier.fillMaxSize()) {", ui_toggle_replacement, 1)

    with open(filepath, 'w') as f:
        f.write(content)

fix_screen('app/src/main/java/com/example/ui/ExperimentScreen.kt', has_camera2=False)
fix_screen('app/src/main/java/com/example/ui/FocusExperimentScreen.kt', has_camera2=True)
