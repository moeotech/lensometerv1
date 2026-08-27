package com.example.ui

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CaptureRequest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.camera2.interop.Camera2CameraControl
import androidx.camera.camera2.interop.Camera2CameraInfo
import androidx.camera.camera2.interop.CaptureRequestOptions
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.example.analysis.FocusAnalyzer
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.util.concurrent.Executors
import kotlin.math.sqrt

data class FocusPoint(
    val focusDistance: Float, // Diopters
    val sharpness: Float,
    val iso: Int,
    val exposureTimeNs: Long,
    val timestamp: Long
)

data class FocusRunResult(
    val noLensPoints: List<FocusPoint>,
    val lensPoints: List<FocusPoint>
) {
    val f0: Float? get() = noLensPoints.maxByOrNull { it.sharpness }?.focusDistance
    val f1: Float? get() = lensPoints.maxByOrNull { it.sharpness }?.focusDistance
    val deltaF: Float? get() = if (f0 != null && f1 != null) f1!! - f0!! else null
    val peakNoLens: Float? get() = noLensPoints.maxByOrNull { it.sharpness }?.sharpness
    val peakLens: Float? get() = lensPoints.maxByOrNull { it.sharpness }?.sharpness
}

enum class FocusV2Step {
    CAPABILITIES,
    SWEEP_NO_LENS,
    SWEEP_WITH_LENS,
    RESULT
}

@SuppressLint("UnsafeOptInUsageError")
@Composable
fun FocusExperimentScreen() {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    var hasCameraPermission by remember {
        mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == android.content.pm.PackageManager.PERMISSION_GRANTED)
    }
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        hasCameraPermission = granted
    }
    LaunchedEffect(Unit) {
        if (!hasCameraPermission) permissionLauncher.launch(Manifest.permission.CAMERA)
    }

    var currentStep by remember { mutableStateOf(FocusV2Step.CAPABILITIES) }
    var currentRunIndex by remember { mutableStateOf(0) }
    
    val runResults = remember { mutableStateListOf<FocusRunResult?>(null, null, null) }
    var currentNoLensPoints = remember { mutableStateListOf<FocusPoint>() }
    var currentLensPoints = remember { mutableStateListOf<FocusPoint>() }

    var manualFocusSupported by remember { mutableStateOf(false) }
    var minFocusDistance by remember { mutableStateOf(0f) }
    var afModes by remember { mutableStateOf("") }
    var aeLockSupported by remember { mutableStateOf(false) }
    var awbLockSupported by remember { mutableStateOf(false) }
    var torchAvailable by remember { mutableStateOf(false) }

    var cameraControlRef by remember { mutableStateOf<CameraControl?>(null) }
    var camera2ControlRef by remember { mutableStateOf<Camera2CameraControl?>(null) }
    var previewRef by remember { mutableStateOf<Preview?>(null) }

    var frameCaptureCallback by remember { mutableStateOf<((ImageProxy) -> Unit)?>(null) }
    val previewView = remember { PreviewView(context).apply { implementationMode = PreviewView.ImplementationMode.COMPATIBLE } }
    
    var isProcessing by remember { mutableStateOf(false) }
    var sweepProgress by remember { mutableStateOf(0f) }

    DisposableEffect(lifecycleOwner) {
        val analysisExecutor = Executors.newSingleThreadExecutor()
        var isDisposed = false
        var imageAnalysisRef: ImageAnalysis? = null
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)

        cameraProviderFuture.addListener({
            if (isDisposed) return@addListener
            val cameraProvider = cameraProviderFuture.get()

            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(previewView.surfaceProvider)
            }
            previewRef = preview

            val imageAnalysis = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also { analysis ->
                    analysis.setAnalyzer(analysisExecutor) { imageProxy ->
                        try {
                            frameCaptureCallback?.invoke(imageProxy)
                        } finally {
                            imageProxy.close()
                        }
                    }
                }
            imageAnalysisRef = imageAnalysis

            try {
                val camera = cameraProvider.bindToLifecycle(
                    lifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageAnalysis
                )
                val cameraInfo = camera.cameraInfo
                cameraControlRef = camera.cameraControl
                
                val cam2Info = Camera2CameraInfo.from(cameraInfo)
                camera2ControlRef = Camera2CameraControl.from(camera.cameraControl)

                minFocusDistance = cam2Info.getCameraCharacteristic(CameraCharacteristics.LENS_INFO_MINIMUM_FOCUS_DISTANCE) ?: 0f
                manualFocusSupported = minFocusDistance > 0f
                torchAvailable = cameraInfo.hasFlashUnit()

                val modes = cam2Info.getCameraCharacteristic(CameraCharacteristics.CONTROL_AF_AVAILABLE_MODES)
                afModes = modes?.joinToString(",") { it.toString() } ?: "None"

                aeLockSupported = cam2Info.getCameraCharacteristic(CameraCharacteristics.CONTROL_AE_LOCK_AVAILABLE) == true
                awbLockSupported = cam2Info.getCameraCharacteristic(CameraCharacteristics.CONTROL_AWB_LOCK_AVAILABLE) == true

            } catch (exc: Exception) {}
        }, ContextCompat.getMainExecutor(context))

        onDispose {
            isDisposed = true
            imageAnalysisRef?.clearAnalyzer()
            try {
                if (cameraProviderFuture.isDone) {
                    val provider = cameraProviderFuture.get()
                    previewRef?.let { provider.unbind(it) }
                    imageAnalysisRef?.let { provider.unbind(it) }
                }
            } catch (e: Exception) {}
            analysisExecutor.shutdown()
        }
    }

    suspend fun runSweep(targetList: androidx.compose.runtime.snapshots.SnapshotStateList<FocusPoint>) {
        isProcessing = true
        sweepProgress = 0f
        targetList.clear()

        // Lock AE/AWB
        val factory = SurfaceOrientedMeteringPointFactory(1f, 1f)
        val action = FocusMeteringAction.Builder(
            factory.createPoint(0.5f, 0.5f),
            FocusMeteringAction.FLAG_AE or FocusMeteringAction.FLAG_AWB
        ).disableAutoCancel().build()
        try { cameraControlRef?.startFocusAndMetering(action) } catch (e: Exception) {}
        
        delay(600) // let exposure settle
        
        val steps = 25
        val stepSize = minFocusDistance / steps
        
        for (i in 0..steps) {
            val dist = i * stepSize
            
            // Set Focus Distance
            val options = CaptureRequestOptions.Builder()
                .setCaptureRequestOption(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF)
                .setCaptureRequestOption(CaptureRequest.LENS_FOCUS_DISTANCE, dist)
                .build()
            try { camera2ControlRef?.captureRequestOptions = options } catch (e: Exception) {}
            
            delay(250) // wait for lens physical movement
            
            var captured = false
            frameCaptureCallback = { proxy ->
                if (!captured) {
                    try {
                        val sharpness = FocusAnalyzer.measureCenterSharpness(proxy)
                        val iso = 0
                        val expTime = 0L
                        
                        targetList.add(FocusPoint(
                            focusDistance = dist,
                            sharpness = sharpness,
                            iso = iso,
                            exposureTimeNs = expTime,
                            timestamp = System.currentTimeMillis()
                        ))
                    } catch (e: Exception) {}
                    captured = true
                }
            }
            
            var timeout = 0
            while (!captured && timeout < 20) {
                delay(50)
                timeout++
            }
            frameCaptureCallback = null
            sweepProgress = (i + 1f) / (steps + 1f)
        }

        // Restore AF
        val options = CaptureRequestOptions.Builder()
            .setCaptureRequestOption(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE)
            .build()
        try { camera2ControlRef?.captureRequestOptions = options } catch (e: Exception) {}
        
        isProcessing = false
    }

    val bgColor = Color(0xFF1C1B1F)
    val textColor = Color(0xFFE6E1E5)
    val primaryColor = Color(0xFFD0BCFF)
    val cardBg = Color(0xFF2B2930)
    val borderColor = Color(0xFF49454F)

    Column(modifier = Modifier.fillMaxSize().background(bgColor).padding(16.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(text = "SCIENTIFIC PROTOTYPE", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = primaryColor, letterSpacing = 2.sp)
                Text(text = "OPTICAL FOCUS V2", fontSize = 18.sp, fontWeight = FontWeight.Light, color = textColor, letterSpacing = (-0.5).sp)
            }
        }

        if (currentStep == FocusV2Step.CAPABILITIES) {
            Column(modifier = Modifier.weight(1f).verticalScroll(rememberScrollState())) {
                Surface(color = cardBg, shape = RoundedCornerShape(24.dp), border = BorderStroke(1.dp, borderColor)) {
                    Column(modifier = Modifier.padding(16.dp).fillMaxWidth()) {
                        ResultSectionTitleV2("CAMERA CAPABILITIES")
                        ResultRowV2("Manual Focus Supported", if (manualFocusSupported) "YES" else "NO")
                        ResultRowV2("Min Focus Distance", String.format("%.2f Diopters", minFocusDistance))
                        ResultRowV2("AF Modes", afModes)
                        ResultRowV2("AE Lock Supported", if (aeLockSupported) "YES" else "NO")
                        ResultRowV2("AWB Lock Supported", if (awbLockSupported) "YES" else "NO")
                        ResultRowV2("Torch Available", if (torchAvailable) "YES" else "NO")
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                if (!manualFocusSupported) {
                    Surface(color = Color(0xFF4A1A1A), shape = RoundedCornerShape(16.dp), border = BorderStroke(1.dp, Color(0xFFFF5252))) {
                        Text("MANUAL_FOCUS_UNAVAILABLE\n\nYour device does not support Camera2 manual focus control. The experiment cannot proceed.", modifier = Modifier.padding(16.dp), color = Color.White)
                    }
                } else {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        (0..2).forEach { runIdx ->
                            Button(
                                onClick = {
                                    currentRunIndex = runIdx
                                    currentNoLensPoints.clear()
                                    currentLensPoints.clear()
                                    currentStep = FocusV2Step.SWEEP_NO_LENS
                                },
                                shape = RoundedCornerShape(16.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = if (runResults[runIdx] == null) primaryColor else Color(0xFF49454F), contentColor = Color(0xFF381E72))
                            ) {
                                Text("RUN ${runIdx + 1}", fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(24.dp))
                    
                    // Show repeatability summary if all 3 runs exist
                    if (runResults.all { it != null }) {
                        val deltas = runResults.mapNotNull { it?.deltaF }
                        if (deltas.size == 3) {
                            val meanDelta = deltas.average().toFloat()
                            val stdDevDelta = sqrt(deltas.map { (it - meanDelta) * (it - meanDelta) }.average()).toFloat()
                            
                            Surface(color = cardBg, shape = RoundedCornerShape(24.dp), border = BorderStroke(1.dp, borderColor)) {
                                Column(modifier = Modifier.padding(16.dp).fillMaxWidth()) {
                                    ResultSectionTitleV2("REPEATABILITY RESULTS")
                                    runResults.forEachIndexed { i, res ->
                                        ResultRowV2("Run ${i+1} DeltaF", String.format("%.3f D", res?.deltaF ?: 0f))
                                    }
                                    Spacer(modifier = Modifier.height(8.dp))
                                    ResultRowV2("MEAN DeltaF", String.format("%.3f D", meanDelta))
                                    ResultRowV2("STD DEV DeltaF", String.format("%.3f D", stdDevDelta))
                                }
                            }
                        }
                    }
                }
            }
        } else if (currentStep == FocusV2Step.SWEEP_NO_LENS || currentStep == FocusV2Step.SWEEP_WITH_LENS) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .clip(RoundedCornerShape(24.dp))
                    .background(Color(0xFF1B1B1F))
                    .border(4.dp, Color.White, RoundedCornerShape(24.dp))
            ) {
                AndroidView(factory = { previewView }, modifier = Modifier.fillMaxSize())

                // Alignment Overlay
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Box(modifier = Modifier.size(120.dp).border(2.dp, Color.Green.copy(alpha = 0.5f), CircleShape))
                    Box(modifier = Modifier.fillMaxWidth(0.6f).fillMaxHeight(0.4f).border(1.dp, Color.Yellow.copy(alpha = 0.5f), RoundedCornerShape(12.dp)))
                    
                    // Center ROI indicator (approx 20%)
                    Box(modifier = Modifier.fillMaxWidth(0.2f).fillMaxHeight(0.2f).background(Color.Red.copy(alpha = 0.2f)).border(1.dp, Color.Red))
                    
                    Text("CENTER ROI", color = Color.Red, fontSize = 10.sp, modifier = Modifier.align(Alignment.Center).offset(y = 40.dp))
                }

                if (isProcessing) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.BottomCenter)
                            .padding(16.dp)
                            .fillMaxWidth()
                            .background(Color.Black.copy(alpha = 0.8f), RoundedCornerShape(12.dp))
                            .padding(12.dp)
                    ) {
                        Column {
                            val phaseText = if (currentStep == FocusV2Step.SWEEP_NO_LENS) "No Lens Sweep" else "With Lens Sweep"
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(text = "$phaseText...", color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                                Text(text = "${(sweepProgress * 100).toInt()}%", color = primaryColor, fontSize = 12.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            LinearProgressIndicator(
                                progress = { sweepProgress },
                                modifier = Modifier.fillMaxWidth().height(4.dp).clip(RoundedCornerShape(2.dp)),
                                color = primaryColor,
                                trackColor = Color.White.copy(alpha = 0.2f)
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
            
            val coroutineScope = rememberCoroutineScope()
            val btnTitle = if (currentStep == FocusV2Step.SWEEP_NO_LENS) "START NO LENS SWEEP" else "START WITH LENS SWEEP"
            
            Button(
                onClick = {
                    if (!isProcessing) {
                        coroutineScope.launch {
                            if (currentStep == FocusV2Step.SWEEP_NO_LENS) {
                                runSweep(currentNoLensPoints)
                                currentStep = FocusV2Step.SWEEP_WITH_LENS
                            } else {
                                runSweep(currentLensPoints)
                                runResults[currentRunIndex] = FocusRunResult(currentNoLensPoints.toList(), currentLensPoints.toList())
                                currentStep = FocusV2Step.RESULT
                            }
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth().height(56.dp),
                shape = RoundedCornerShape(16.dp),
                colors = ButtonDefaults.buttonColors(containerColor = primaryColor, contentColor = Color(0xFF381E72)),
                enabled = !isProcessing
            ) {
                Text(text = if (isProcessing) "SWEEPING..." else btnTitle, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            }
        } else if (currentStep == FocusV2Step.RESULT) {
            val result = runResults[currentRunIndex]
            Column(modifier = Modifier.weight(1f).verticalScroll(rememberScrollState())) {
                Surface(color = cardBg, shape = RoundedCornerShape(24.dp), border = BorderStroke(1.dp, borderColor)) {
                    Column(modifier = Modifier.padding(16.dp).fillMaxWidth()) {
                        ResultSectionTitleV2("RUN ${currentRunIndex + 1} RESULT")
                        
                        ResultRowV2("NO LENS BEST FOCUS (F0)", String.format("%.3f", result?.f0 ?: 0f))
                        ResultRowV2("WITH LENS BEST FOCUS (F1)", String.format("%.3f", result?.f1 ?: 0f))
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        ResultRowV2("FOCUS SHIFT (F1 - F0)", String.format("%.3f", result?.deltaF ?: 0f))
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        ResultRowV2("Peak Sharpness No Lens", String.format("%.1f", result?.peakNoLens ?: 0f))
                        ResultRowV2("Peak Sharpness With Lens", String.format("%.1f", result?.peakLens ?: 0f))
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                FocusGraph("Focus Distance vs Sharpness", result?.noLensPoints ?: emptyList(), result?.lensPoints ?: emptyList())
                
                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = { currentStep = FocusV2Step.CAPABILITIES },
                    modifier = Modifier.fillMaxWidth().height(48.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = primaryColor, contentColor = Color(0xFF381E72))
                ) {
                    Text(text = "BACK TO CAPABILITIES", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun FocusGraph(title: String, noLens: List<FocusPoint>, withLens: List<FocusPoint>) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
        Text(text = title, fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFFCAC4D0))
        Spacer(modifier = Modifier.height(4.dp))
        Canvas(modifier = Modifier.fillMaxWidth().height(150.dp).background(Color(0xFF1C1B1F), RoundedCornerShape(8.dp)).border(1.dp, Color(0xFF49454F), RoundedCornerShape(8.dp))) {
            val allPoints = noLens + withLens
            if (allPoints.isEmpty()) return@Canvas
            
            val maxSharp = allPoints.maxOfOrNull { it.sharpness } ?: 1f
            val minSharp = allPoints.minOfOrNull { it.sharpness } ?: 0f
            val maxDist = allPoints.maxOfOrNull { it.focusDistance } ?: 1f
            val minDist = allPoints.minOfOrNull { it.focusDistance } ?: 0f
            
            val sharpRange = (maxSharp - minSharp).coerceAtLeast(0.1f)
            val distRange = (maxDist - minDist).coerceAtLeast(0.1f)
            
            fun drawCurve(pts: List<FocusPoint>, color: Color) {
                if (pts.size < 2) return
                val path = Path()
                val sorted = pts.sortedBy { it.focusDistance }
                sorted.forEachIndexed { index, pt ->
                    val x = ((pt.focusDistance - minDist) / distRange) * size.width
                    val y = size.height - ((pt.sharpness - minSharp) / sharpRange) * size.height
                    if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
                }
                drawPath(path, color, style = Stroke(width = 2.dp.toPx(), cap = StrokeCap.Round, join = StrokeJoin.Round))
            }
            
            drawCurve(noLens, Color(0xFFD0BCFF)) // Primary purple for No Lens
            drawCurve(withLens, Color(0xFF4DB6AC)) // Teal for With Lens
        }
        Row(modifier = Modifier.fillMaxWidth().padding(top = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("No Lens", color = Color(0xFFD0BCFF), fontSize = 9.sp, fontWeight = FontWeight.Bold)
            Text("With Lens", color = Color(0xFF4DB6AC), fontSize = 9.sp, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
fun ResultSectionTitleV2(title: String) {
    Text(
        text = title,
        fontSize = 11.sp,
        fontWeight = FontWeight.Black,
        color = Color(0xFFD0BCFF),
        letterSpacing = 1.sp
    )
    Spacer(modifier = Modifier.height(8.dp))
}

@Composable
fun ResultRowV2(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = label, fontSize = 13.sp, color = Color(0xFFCAC4D0))
        Text(text = value, fontSize = 13.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold, color = Color(0xFFE6E1E5))
    }
}
