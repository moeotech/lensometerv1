cat << 'INNER_EOF' > app/src/main/java/com/example/ui/LensExperimentScreen.kt
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
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import com.example.analysis.LensAnalyzer
import com.example.model.LensMeasurementResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executors
import kotlin.math.*

enum class LensExperimentPhase {
    ALIGN_NO_LENS,
    CAPTURE_NO_LENS,
    ALIGN_LENS,
    CAPTURE_LENS,
    PROCESSING,
    RESULTS
}

@Composable
fun LensExperimentScreen() {
    val context = LocalContext.current
    val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current
    val coroutineScope = rememberCoroutineScope()

    var phase by remember { mutableStateOf(LensExperimentPhase.ALIGN_NO_LENS) }
    
    val noLensFrames = remember { mutableListOf<Bitmap>() }
    val withLensFrames = remember { mutableListOf<Bitmap>() }
    
    var previewRef by remember { mutableStateOf<Preview?>(null) }
    var cameraControlRef by remember { mutableStateOf<CameraControl?>(null) }
    var camera2ControlRef by remember { mutableStateOf<Camera2CameraControl?>(null) }
    
    var focusDistance by remember { mutableStateOf(0f) }
    
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

            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                if (isDisposed) return@postDelayed
                val preview = Preview.Builder().build()
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
            }, 300)
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

    suspend fun runCaptureSequence(targetList: MutableList<Bitmap>) {
        targetList.clear()
        
        // Lock Focus/AE
        camera2ControlRef?.let { c2c ->
            val builder = CaptureRequestOptions.Builder()
            builder.setCaptureRequestOption(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF)
            builder.setCaptureRequestOption(CaptureRequest.LENS_FOCUS_DISTANCE, focusDistance)
            builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_OFF)
            builder.setCaptureRequestOption(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_OFF)
            c2c.captureRequestOptions = builder.build()
        }
        
        delay(500)
        
        withContext(Dispatchers.Default) {
            for (i in 0 until 30) {
                var capturedBitmap: Bitmap? = null
                val lock = java.util.concurrent.CountDownLatch(1)
                frameCaptureCallback = { proxy ->
                    if (capturedBitmap == null) {
                        capturedBitmap = proxyToBitmap(proxy)
                        lock.countDown()
                    }
                }
                lock.await(1000, java.util.concurrent.TimeUnit.MILLISECONDS)
                frameCaptureCallback = null
                
                capturedBitmap?.let { targetList.add(it) }
                delay(10)
            }
        }
        
        // Restore Auto
        camera2ControlRef?.let { c2c ->
            val builder = CaptureRequestOptions.Builder()
            builder.setCaptureRequestOption(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE)
            builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON)
            builder.setCaptureRequestOption(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_AUTO)
            c2c.captureRequestOptions = builder.build()
        }
    }

    Box(modifier = Modifier.fillMaxSize().background(Color.Black)) {
        if (phase == LensExperimentPhase.ALIGN_NO_LENS || phase == LensExperimentPhase.ALIGN_LENS) {
            AndroidView(
                factory = { ctx ->
                    PreviewView(ctx).apply {
                        this.scaleType = PreviewView.ScaleType.FIT_CENTER
                        previewRef?.setSurfaceProvider(this.surfaceProvider)
                    }
                },
                modifier = Modifier.fillMaxSize(),
                update = { view ->
                    previewRef?.setSurfaceProvider(view.surfaceProvider)
                }
            )
            
            // Alignment Guide
            Canvas(modifier = Modifier.fillMaxSize()) {
                val cx = size.width / 2
                val cy = size.height / 2
                val radius = min(size.width, size.height) * 0.35f
                
                drawCircle(
                    color = if (phase == LensExperimentPhase.ALIGN_NO_LENS) Color.Yellow else Color.Cyan,
                    radius = radius,
                    center = Offset(cx, cy),
                    style = Stroke(width = 4f)
                )
                
                drawLine(Color.Red, Offset(cx - 20, cy), Offset(cx + 20, cy), 2f)
                drawLine(Color.Red, Offset(cx, cy - 20), Offset(cx, cy + 20), 2f)
            }
            
            Column(modifier = Modifier.align(Alignment.BottomCenter).padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = if (phase == LensExperimentPhase.ALIGN_NO_LENS) "ALIGN PRINTED TARGET (NO LENS)" else "PLACE LENS IN CIRCLE",
                    color = Color.White, fontWeight = FontWeight.Bold,
                    modifier = Modifier.background(Color(0x88000000), RoundedCornerShape(8.dp)).padding(16.dp)
                )
                Spacer(modifier = Modifier.height(16.dp))
                Button(onClick = {
                    coroutineScope.launch {
                        if (phase == LensExperimentPhase.ALIGN_NO_LENS) {
                            phase = LensExperimentPhase.CAPTURE_NO_LENS
                            runCaptureSequence(noLensFrames)
                            phase = LensExperimentPhase.ALIGN_LENS
                        } else {
                            phase = LensExperimentPhase.CAPTURE_LENS
                            runCaptureSequence(withLensFrames)
                            phase = LensExperimentPhase.PROCESSING
                            val res = withContext(Dispatchers.Default) {
                                LensAnalyzer.analyze(noLensFrames, withLensFrames)
                            }
                            runResults.add(res)
                            phase = LensExperimentPhase.RESULTS
                        }
                    }
                }) {
                    Text(if (phase == LensExperimentPhase.ALIGN_NO_LENS) "CAPTURE BASE" else "CAPTURE LENS")
                }
            }
        } else if (phase == LensExperimentPhase.CAPTURE_NO_LENS || phase == LensExperimentPhase.CAPTURE_LENS || phase == LensExperimentPhase.PROCESSING) {
            Column(modifier = Modifier.align(Alignment.Center), horizontalAlignment = Alignment.CenterHorizontally) {
                CircularProgressIndicator(color = Color.White)
                Spacer(modifier = Modifier.height(16.dp))
                Text(phase.name, color = Color.White)
            }
        } else if (phase == LensExperimentPhase.RESULTS) {
            var showDebug by remember { mutableStateOf(false) }
            
            LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                item {
                    Text("V3.1 RESULTS", color = Color.White, fontSize = 24.sp, fontWeight = FontWeight.Bold)
                    Text("Runs completed: ${runResults.size} / $maxRuns", color = Color.Gray)
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    if (runResults.isNotEmpty()) {
                        val res = runResults.last()
                        
                        ResultRow("TRACKED DOTS", "${res.trackedPoints}")
                        ResultRow("COVERAGE", "${res.coverage}%")
                        ResultRow("REGISTRATION RMS", String.format("%.2f px", res.registrationRms))
                        ResultRow("RANSAC INLIERS", "${res.ransacInliers}")
                        Spacer(modifier = Modifier.height(16.dp))
                        ResultRow("PRINCIPAL SIGNAL 1", String.format("%.5f (%.0f°)", res.p1, res.p1Angle))
                        ResultRow("PRINCIPAL SIGNAL 2", String.format("%.5f (%.0f°)", res.p2, res.p2Angle))
                        ResultRow("ANISOTROPY", String.format("%.5f", abs(res.p1 - res.p2)))
                        ResultRow("ISOTROPIC COMP", String.format("%.5f", (res.p1 + res.p2)/2))
                        Spacer(modifier = Modifier.height(16.dp))
                        ResultRow("GEOMETRIC CENTER", String.format("%.1f, %.1f", res.geometricCenterX, res.geometricCenterY))
                        ResultRow("OPTICAL CENTER", String.format("%.1f, %.1f", res.opticalCenterX, res.opticalCenterY))
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        Button(onClick = { showDebug = !showDebug }, modifier = Modifier.fillMaxWidth()) {
                            Text(if (showDebug) "Hide Vector Debug" else "Show Vector Debug")
                        }
                        
                        if (showDebug && res.vectors.isNotEmpty()) {
                            var magFactor by remember { mutableStateOf(5f) }
                            Spacer(modifier = Modifier.height(16.dp))
                            Text("Vector Magnification: ${magFactor.toInt()}x", color = Color.White)
                            Slider(value = magFactor, onValueChange = { magFactor = it }, valueRange = 1f..20f)
                            
                            Box(modifier = Modifier.fillMaxWidth().aspectRatio(res.imageWidth.toFloat() / res.imageHeight.toFloat()).border(1.dp, Color.Gray)) {
                                Canvas(modifier = Modifier.fillMaxSize()) {
                                    val scaleX = size.width / res.imageWidth
                                    val scaleY = size.height / res.imageHeight
                                    
                                    drawCircle(Color.DarkGray, res.lensRadius.toFloat() * scaleX, Offset(res.geometricCenterX.toFloat() * scaleX, res.geometricCenterY.toFloat() * scaleY), style = Stroke(2f))
                                    drawCircle(Color.Magenta, 10f, Offset(res.opticalCenterX.toFloat() * scaleX, res.opticalCenterY.toFloat() * scaleY))
                                    
                                    val oc = Offset(res.opticalCenterX.toFloat() * scaleX, res.opticalCenterY.toFloat() * scaleY)
                                    val axLen = res.lensRadius.toFloat() * scaleX
                                    val rad1 = res.p1Angle * Math.PI / 180.0
                                    val rad2 = res.p2Angle * Math.PI / 180.0
                                    drawLine(Color.Cyan, oc - Offset((cos(rad1)*axLen).toFloat(), (sin(rad1)*axLen).toFloat()), oc + Offset((cos(rad1)*axLen).toFloat(), (sin(rad1)*axLen).toFloat()), 3f)
                                    drawLine(Color.Yellow, oc - Offset((cos(rad2)*axLen).toFloat(), (sin(rad2)*axLen).toFloat()), oc + Offset((cos(rad2)*axLen).toFloat(), (sin(rad2)*axLen).toFloat()), 3f)
                                    
                                    for (v in res.vectors) {
                                        val start = Offset(v.rx.toFloat() * scaleX, v.ry.toFloat() * scaleY)
                                        val dx = (v.ox - v.rx).toFloat() * scaleX * magFactor
                                        val dy = (v.oy - v.ry).toFloat() * scaleY * magFactor
                                        val end = start + Offset(dx, dy)
                                        drawLine(Color.Red, start, end, 2f)
                                        drawCircle(Color.White, 3f, start)
                                    }
                                }
                            }
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(32.dp))
                    
                    if (runResults.size >= 3) {
                        Text("REPEATABILITY GATES", color = Color.White, fontWeight = FontWeight.Bold)
                        
                        val p1Mean = runResults.map { it.p1 }.average()
                        val p2Mean = runResults.map { it.p2 }.average()
                        val p1Std = Math.sqrt(runResults.map { Math.pow(it.p1 - p1Mean, 2.0) }.average())
                        
                        var sumSin = 0.0
                        var sumCos = 0.0
                        runResults.forEach {
                            val rad = 2 * it.p1Angle * Math.PI / 180.0
                            sumSin += sin(rad)
                            sumCos += cos(rad)
                        }
                        val meanAxisRad = Math.atan2(sumSin, sumCos) / 2.0
                        var meanAxisDeg = meanAxisRad * 180.0 / Math.PI
                        if (meanAxisDeg < 0) meanAxisDeg += 180.0
                        val R = Math.sqrt(sumSin*sumSin + sumCos*sumCos) / runResults.size
                        val angularDev = Math.sqrt(-2.0 * Math.log(R)) * 180.0 / Math.PI / 2.0
                        
                        val ocxMean = runResults.map { it.opticalCenterX }.average()
                        val ocyMean = runResults.map { it.opticalCenterY }.average()
                        val ocStd = Math.sqrt(runResults.map { hypot(it.opticalCenterX - ocxMean, it.opticalCenterY - ocyMean).pow(2) }.average())
                        
                        ResultRow("P1 Mean", String.format("%.5f ± %.5f", p1Mean, p1Std))
                        ResultRow("P2 Mean", String.format("%.5f", p2Mean))
                        ResultRow("AXIS Mean", String.format("%.0f° ± %.1f°", meanAxisDeg, angularDev))
                        ResultRow("OPT CENTER Std", String.format("%.1f px", ocStd))
                        
                        val pass = (p1Std < 0.02 && angularDev < 15.0 && ocStd < 100.0)
                        Text(
                            if (pass) "REPEATABILITY PASS" else "REPEATABILITY FAILED", 
                            color = if (pass) Color.Green else Color.Red, 
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(vertical = 16.dp)
                        )
                    }
                    
                    if (runResults.size < maxRuns) {
                        Button(
                            onClick = { phase = LensExperimentPhase.ALIGN_NO_LENS },
                            modifier = Modifier.fillMaxWidth().padding(vertical = 16.dp)
                        ) {
                            Text("START RUN ${runResults.size + 1}")
                        }
                    } else {
                        Button(
                            onClick = { runResults.clear(); phase = LensExperimentPhase.ALIGN_NO_LENS },
                            modifier = Modifier.fillMaxWidth().padding(vertical = 16.dp)
                        ) {
                            Text("RESET EXPERIMENT")
                        }
                    }
                }
            }
        }
    }
}

// ResultRow is already declared in ExperimentScreen.kt

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
INNER_EOF
