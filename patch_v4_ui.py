import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

# Add analysisErrorMessage state
state_search = """    var currentStep by remember { mutableStateOf(V4Step.INIT) }"""
state_replacement = """    var currentStep by remember { mutableStateOf(V4Step.INIT) }
    var analysisErrorMessage by remember { mutableStateOf("") }"""
content = content.replace(state_search, state_replacement)

# Modify ANALYZING step
analyzing_search = """                V4Step.ANALYZING -> {
                    Text("ANALYZING...", color = Color.Cyan)
                    LaunchedEffect(Unit) {
                        coroutineScope.launch {
                            val result = V4OpticalAnalyzer.analyze(noLensFrames, withLensFrames)
                            runResults[currentRunIndex] = result
                            if (currentRunIndex < 2) {
                                currentRunIndex++
                                currentStep = V4Step.STEP_1_NO_LENS
                                noLensFrames.clear()
                                withLensFrames.clear()
                                // Unlock AE for next run
                                camera2ControlRef?.let { c2c ->
                                    val builder = CaptureRequestOptions.Builder()
                                    builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_LOCK, false)
                                    builder.setCaptureRequestOption(CaptureRequest.CONTROL_AWB_LOCK, false)
                                    builder.setCaptureRequestOption(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE)
                                    c2c.captureRequestOptions = builder.build()
                                }
                            } else {
                                overallResult = V4OpticalAnalyzer.calculateRepeatability(runResults.filterNotNull())
                                currentStep = V4Step.COMPLETE
                            }
                        }
                    }
                }"""

analyzing_replacement = """                V4Step.ANALYZING -> {
                    Text("ANALYZING...", color = Color.Cyan)
                    LaunchedEffect(Unit) {
                        coroutineScope.launch {
                            val result = V4OpticalAnalyzer.analyze(noLensFrames, withLensFrames)
                            
                            if (!result.success) {
                                analysisErrorMessage = "INSUFFICIENT OPTICAL FEATURES - HOLD STILL\\n${result.errorMessage}"
                                // Retry same run
                                currentStep = V4Step.STEP_1_NO_LENS
                                noLensFrames.clear()
                                withLensFrames.clear()
                                camera2ControlRef?.let { c2c ->
                                    val builder = CaptureRequestOptions.Builder()
                                    builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_LOCK, false)
                                    builder.setCaptureRequestOption(CaptureRequest.CONTROL_AWB_LOCK, false)
                                    builder.setCaptureRequestOption(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE)
                                    c2c.captureRequestOptions = builder.build()
                                }
                            } else {
                                analysisErrorMessage = ""
                                runResults[currentRunIndex] = result
                                if (currentRunIndex < 2) {
                                    currentRunIndex++
                                    currentStep = V4Step.STEP_1_NO_LENS
                                    noLensFrames.clear()
                                    withLensFrames.clear()
                                    // Unlock AE for next run
                                    camera2ControlRef?.let { c2c ->
                                        val builder = CaptureRequestOptions.Builder()
                                        builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_LOCK, false)
                                        builder.setCaptureRequestOption(CaptureRequest.CONTROL_AWB_LOCK, false)
                                        builder.setCaptureRequestOption(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE)
                                        c2c.captureRequestOptions = builder.build()
                                    }
                                } else {
                                    val validRuns = runResults.filterNotNull().filter { it.success }
                                    overallResult = V4OpticalAnalyzer.calculateRepeatability(validRuns)
                                    currentStep = V4Step.COMPLETE
                                }
                            }
                        }
                    }
                }"""
content = content.replace(analyzing_search, analyzing_replacement)

# Display analysisErrorMessage above step controls if not empty
controls_search = """                if (currentStep == V4Step.STEP_1_NO_LENS) {"""
controls_replacement = """                if (analysisErrorMessage.isNotEmpty() && currentStep != V4Step.COMPLETE && currentStep != V4Step.ANALYZING) {
                    Text(analysisErrorMessage, color = Color.Red, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 16.dp))
                }
                if (currentStep == V4Step.STEP_1_NO_LENS) {"""
content = content.replace(controls_search, controls_replacement)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
