package com.example.ui

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Rect
import android.graphics.YuvImage
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CaptureRequest
import android.media.Image
import androidx.camera.camera2.interop.Camera2CameraControl
import androidx.camera.camera2.interop.Camera2CameraInfo
import androidx.camera.camera2.interop.CaptureRequestOptions
import androidx.camera.core.CameraControl
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.example.analysis.LensAnalyzer
import com.example.model.LensMeasurementResult
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.io.File
import java.util.concurrent.Executors
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

enum class LensScanPhase {
    NO_LENS_ALIGN,
    NO_LENS_CAPTURE,
    WITH_LENS_ALIGN,
    WITH_LENS_CAPTURE,
    RESULTS
}

@Composable
fun LensExperimentScreen() {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val scope = rememberCoroutineScope()

    var currentPhase by remember { mutableStateOf(LensScanPhase.NO_LENS_ALIGN) }
    
    var cameraControlRef by remember { mutableStateOf<CameraControl?>(null) }
    var camera2ControlRef by remember { mutableStateOf<Camera2CameraControl?>(null) }
    var previewRef by remember { mutableStateOf<Preview?>(null) }

    val previewView = remember { PreviewView(context).apply { implementationMode = PreviewView.ImplementationMode.COMPATIBLE } }

    var alignmentInstruction by remember { mutableStateOf("TARGET NOT DETECTED") }
    var alignmentColor by remember { mutableStateOf(Color.Red) }
    var isStable by remember { mutableStateOf(false) }
    var stableTimeMs by remember { mutableStateOf(0L) }
    var lastFrameTime by remember { mutableStateOf(0L) }
    
    var showDebug by remember { mutableStateOf(false) }

    var noLensFrames by remember { mutableStateOf<List<Bitmap>>(emptyList()) }
    var withLensFrames by remember { mutableStateOf<List<Bitmap>>(emptyList()) }
    var measurementResult by remember { mutableStateOf<LensMeasurementResult?>(null) }

    var runCount by remember { mutableStateOf(0) }
    val maxRuns = 3
    var runResults by remember { mutableStateOf(mutableListOf<LensMeasurementResult>()) }

    var frameCaptureCallback by remember { mutableStateOf<((ImageProxy) -> Unit)?>(null) }

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
                cameraControlRef = camera.cameraControl
                camera2ControlRef = Camera2CameraControl.from(camera.cameraControl)
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

    // Alignment and stability logic
    LaunchedEffect(currentPhase) {
        if (currentPhase == LensScanPhase.NO_LENS_ALIGN || currentPhase == LensScanPhase.WITH_LENS_ALIGN) {
            frameCaptureCallback = { proxy ->
                val currentTime = System.currentTimeMillis()
                
                // Mock alignment for now: wait for stability
                // In a real scenario, we'd analyze proxy for target presence
                val instruction = if (currentPhase == LensScanPhase.NO_LENS_ALIGN) "HOLD STILL - NO LENS" else "HOLD STILL - WITH LENS"
                
                if (instruction == alignmentInstruction) {
                    stableTimeMs += (currentTime - lastFrameTime)
                } else {
                    alignmentInstruction = instruction
                    stableTimeMs = 0
                }
                lastFrameTime = currentTime
                
                isStable = stableTimeMs > 800
                alignmentColor = if (isStable) Color.Green else Color.Red
                
                if (isStable) {
                    if (currentPhase == LensScanPhase.NO_LENS_ALIGN) {
                        currentPhase = LensScanPhase.NO_LENS_CAPTURE
                    } else if (currentPhase == LensScanPhase.WITH_LENS_ALIGN) {
                        currentPhase = LensScanPhase.WITH_LENS_CAPTURE
                    }
                }
            }
        }
    }

    // Capture logic
    LaunchedEffect(currentPhase) {
        if (currentPhase == LensScanPhase.NO_LENS_CAPTURE || currentPhase == LensScanPhase.WITH_LENS_CAPTURE) {
            val captured = mutableListOf<Bitmap>()
            
            // Lock AE / AWB
            val options = CaptureRequestOptions.Builder()
                .setCaptureRequestOption(CaptureRequest.CONTROL_AE_LOCK, true)
                .setCaptureRequestOption(CaptureRequest.CONTROL_AWB_LOCK, true)
                .build()
            try { camera2ControlRef?.captureRequestOptions = options } catch (e: Exception) {}

            frameCaptureCallback = { proxy ->
                if (captured.size < 30) {
                    val bitmap = proxyToBitmap(proxy)
                    if (bitmap != null) {
                        captured.add(bitmap)
                    }
                }
            }
            
            while(captured.size < 30) {
                delay(50)
            }
            
            frameCaptureCallback = null

            // Unlock AE / AWB
            val unlockOptions = CaptureRequestOptions.Builder()
                .setCaptureRequestOption(CaptureRequest.CONTROL_AE_LOCK, false)
                .setCaptureRequestOption(CaptureRequest.CONTROL_AWB_LOCK, false)
                .build()
            try { camera2ControlRef?.captureRequestOptions = unlockOptions } catch (e: Exception) {}

            if (currentPhase == LensScanPhase.NO_LENS_CAPTURE) {
                noLensFrames = captured
                currentPhase = LensScanPhase.WITH_LENS_ALIGN
                stableTimeMs = 0
            } else {
                withLensFrames = captured
                // Process the frames
                currentPhase = LensScanPhase.RESULTS
                scope.launch {
                    val result = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Default) {
                        LensAnalyzer.analyze(noLensFrames, withLensFrames)
                    }
                    measurementResult = result
                    runResults.add(result)
                    runCount++
                }
            }
        }
    }

    val bgColor = Color(0xFF1C1B1F)
    val textColor = Color(0xFFE6E1E5)
    val cardBg = Color(0xFF2B2930)

    Column(modifier = Modifier.fillMaxSize().background(bgColor)) {
        if (currentPhase != LensScanPhase.RESULTS) {
            Box(modifier = Modifier.weight(1f)) {
                AndroidView(factory = { previewView }, modifier = Modifier.fillMaxSize())
                
                // Biometric alignment overlay
                Canvas(modifier = Modifier.fillMaxSize()) {
                    val w = size.width
                    val h = size.height
                    
                    val radius = w * 0.35f
                    val cx = w / 2f
                    val cy = h / 2f
                    
                    // Crosshair
                    drawLine(alignmentColor, Offset(cx - 20f, cy), Offset(cx + 20f, cy), strokeWidth = 5f)
                    drawLine(alignmentColor, Offset(cx, cy - 20f), Offset(cx, cy + 20f), strokeWidth = 5f)
                    
                    // Lens oval/circle
                    drawCircle(alignmentColor, radius, center = Offset(cx, cy), style = Stroke(width = 8f))
                }
                
                Column(
                    modifier = Modifier.fillMaxWidth().align(Alignment.BottomCenter).padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = alignmentInstruction,
                        color = alignmentColor,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.background(Color.Black.copy(alpha = 0.5f)).padding(8.dp)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    if (currentPhase == LensScanPhase.NO_LENS_CAPTURE || currentPhase == LensScanPhase.WITH_LENS_CAPTURE) {
                        CircularProgressIndicator(color = alignmentColor)
                        Text(text = "CAPTURING 30 FRAMES...", color = Color.White, modifier = Modifier.padding(top=8.dp))
                    }
                }
            }
        } else {
            // Results screen
            LazyColumn(modifier = Modifier.weight(1f).padding(16.dp)) {
                item {
                    Text("EXPERIMENTAL LENS RESULT", fontSize = 24.sp, color = textColor, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(16.dp))
                }

                item {
                    val res = measurementResult
                    if (res != null) {
                        ResultRow("SPH", if (res.calibrated) String.format("%.2f D", res.sph) else "NOT CALIBRATED")
                        ResultRow("CYL", if (res.calibrated) String.format("%.2f D", res.cyl) else "NOT CALIBRATED")
                        ResultRow("AXIS", if (res.calibrated) String.format("%.0f°", res.axis) else "NOT CALIBRATED")
                        Spacer(modifier = Modifier.height(16.dp))
                        ResultRow("Confidence", res.confidence)
                        ResultRow("Tracked Points", "${res.trackedPoints}")
                        ResultRow("Mean dx", String.format("%.3f px", res.meanDx))
                        ResultRow("Mean dy", String.format("%.3f px", res.meanDy))
                        ResultRow("Max Displacement", String.format("%.3f px", res.maxDisplacement))
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        Text("PRINCIPAL MERIDIANS", color = textColor, fontWeight = FontWeight.Bold)
                        ResultRow("Signal 1", String.format("%.5f (%.0f°)", res.p1, res.p1Angle))
                        ResultRow("Signal 2", String.format("%.5f (%.0f°)", res.p2, res.p2Angle))
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("DIRECTIONAL SIGNAL", color = textColor, fontWeight = FontWeight.Bold)
                        res.directionalSignals.forEach { (angle, signal) ->
                            ResultRow("$angle°", String.format("%.5f", signal))
                        }
                        
                        Spacer(modifier = Modifier.height(24.dp))
                        Button(onClick = { showDebug = !showDebug }) {
                            Text(if (showDebug) "HIDE SCIENTIFIC DEBUG DATA" else "SCIENTIFIC DEBUG DATA")
                        }
                        if (showDebug) {
                            Column(modifier = Modifier.fillMaxWidth().padding(8.dp).background(Color.Black).padding(8.dp)) {
                                Text("RAW OPTICAL DATA", color = Color.White, fontWeight = FontWeight.Bold)
                                ResultRow("Tracked Points", "${res.trackedPoints}")
                                ResultRow("Mean dx", String.format("%.3f", res.meanDx))
                                ResultRow("Mean dy", String.format("%.3f", res.meanDy))
                                ResultRow("p1", String.format("%.5f", res.p1))
                                ResultRow("p2", String.format("%.5f", res.p2))
                            }
                        }
                    } else {
                        CircularProgressIndicator(color = Color.White)
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("PROCESSING...", color = Color.White)
                    }
                }
                
                item {
                    Spacer(modifier = Modifier.height(24.dp))
                    Button(onClick = {
                        if (runCount < maxRuns) {
                            currentPhase = LensScanPhase.NO_LENS_ALIGN
                        } else {
                            runCount = 0
                            runResults.clear()
                            currentPhase = LensScanPhase.NO_LENS_ALIGN
                        }
                    }) {
                        Text(if (runCount < maxRuns) "RUN ${runCount + 1}" else "RESTART EXPERIMENT")
                    }
                }
                
                if (runResults.size == 3) {
                    item {
                        Spacer(modifier = Modifier.height(24.dp))
                        Text("REPEATABILITY (3 RUNS)", fontSize = 20.sp, color = textColor, fontWeight = FontWeight.Bold)
                        
                        // Compute stats
                        val meanSph = runResults.map { it.sph }.average()
                        val stdSph = Math.sqrt(runResults.map { Math.pow(it.sph - meanSph, 2.0) }.average())
                        val meanCyl = runResults.map { it.cyl }.average()
                        val stdCyl = Math.sqrt(runResults.map { Math.pow(it.cyl - meanCyl, 2.0) }.average())
                        
                        // Circular mean for axis
                        var sumSin = 0.0
                        var sumCos = 0.0
                        runResults.forEach {
                            val rad = 2 * it.axis * PI / 180.0
                            sumSin += sin(rad)
                            sumCos += cos(rad)
                        }
                        val meanAxisRad = Math.atan2(sumSin, sumCos) / 2.0
                        var meanAxisDeg = meanAxisRad * 180.0 / PI
                        if (meanAxisDeg < 0) meanAxisDeg += 180.0
                        
                        val R = Math.sqrt(sumSin*sumSin + sumCos*sumCos) / runResults.size
                        val circularVar = 1.0 - R
                        val angularDev = Math.sqrt(-2.0 * Math.log(R)) * 180.0 / PI / 2.0
                        
                        ResultRow("SPH Mean", String.format("%.2f ± %.2f D", meanSph, stdSph))
                        ResultRow("CYL Mean", String.format("%.2f ± %.2f D", meanCyl, stdCyl))
                        ResultRow("AXIS Mean", String.format("%.0f° ± %.1f°", meanAxisDeg, angularDev))
                        
                        Spacer(modifier = Modifier.height(24.dp))
                        Button(onClick = {
                            saveExperimentData(context, runResults)
                        }) {
                            Text("EXPORT EXPERIMENT DATA")
                        }
                    }
                }
            }
        }
    }
}

fun saveExperimentData(context: Context, results: List<LensMeasurementResult>) {
    try {
        val file = File(context.filesDir, "lens_experiment_data_${System.currentTimeMillis()}.json")
        val sb = StringBuilder()
        sb.append("[\n")
        results.forEachIndexed { index, res ->
            sb.append("  {\n")
            sb.append("    \"sph\": ${res.sph},\n")
            sb.append("    \"cyl\": ${res.cyl},\n")
            sb.append("    \"axis\": ${res.axis},\n")
            sb.append("    \"trackedPoints\": ${res.trackedPoints},\n")
            sb.append("    \"meanDx\": ${res.meanDx},\n")
            sb.append("    \"meanDy\": ${res.meanDy},\n")
            sb.append("    \"directionalSignals\": {\n")
            val signals = res.directionalSignals.entries.toList()
            signals.forEachIndexed { sIdx, (k, v) ->
                sb.append("      \"$k\": $v")
                if (sIdx < signals.size - 1) sb.append(",")
                sb.append("\n")
            }
            sb.append("    }\n")
            sb.append("  }")
            if (index < results.size - 1) sb.append(",")
            sb.append("\n")
        }
        sb.append("]\n")
        file.writeText(sb.toString())
    } catch (e: Exception) {}
}



fun proxyToBitmap(image: ImageProxy): Bitmap? {
    val planeProxy = image.planes
    val yBuffer = planeProxy[0].buffer
    val uBuffer = planeProxy[1].buffer
    val vBuffer = planeProxy[2].buffer

    val ySize = yBuffer.remaining()
    val uSize = uBuffer.remaining()
    val vSize = vBuffer.remaining()

    val nv21 = ByteArray(ySize + uSize + vSize)

    yBuffer.get(nv21, 0, ySize)
    vBuffer.get(nv21, ySize, vSize)
    uBuffer.get(nv21, ySize + vSize, uSize)

    val yuvImage = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
    val out = ByteArrayOutputStream()
    yuvImage.compressToJpeg(Rect(0, 0, yuvImage.width, yuvImage.height), 100, out)
    val imageBytes = out.toByteArray()
    
    val bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
    
    val matrix = android.graphics.Matrix()
    matrix.postRotate(image.imageInfo.rotationDegrees.toFloat())
    return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
}
