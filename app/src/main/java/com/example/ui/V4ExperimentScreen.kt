package com.example.ui

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Bitmap
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
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.example.analysis.V4OpticalAnalyzer
import com.example.analysis.V4Result
import com.example.analysis.V4RunResult
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.util.concurrent.Executors
import kotlin.math.sqrt

enum class V4Step {
    INIT,
    STEP_1_NO_LENS,
    STEP_2_WITH_LENS,
    ANALYZING,
    COMPLETE
}

@SuppressLint("UnsafeOptInUsageError")
@Composable
fun V4ExperimentScreen() {
    val context = LocalContext.current
    val lifecycleOwner = androidx.lifecycle.compose.LocalLifecycleOwner.current

    var hasCameraPermission by remember {
        mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == android.content.pm.PackageManager.PERMISSION_GRANTED)
    }
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        hasCameraPermission = granted
    }
    LaunchedEffect(Unit) {
        if (!hasCameraPermission) permissionLauncher.launch(Manifest.permission.CAMERA)
    }

    var currentStep by remember { mutableStateOf(V4Step.INIT) }
    var currentRunIndex by remember { mutableStateOf(0) }
    
    val runResults = remember { mutableStateListOf<V4RunResult?>(null, null, null) }
    var overallResult by remember { mutableStateOf<V4Result?>(null) }
    
    val noLensFrames = remember { mutableStateListOf<Bitmap>() }
    val withLensFrames = remember { mutableStateListOf<Bitmap>() }
    
    var cameraControlRef by remember { mutableStateOf<CameraControl?>(null) }
    var camera2ControlRef by remember { mutableStateOf<Camera2CameraControl?>(null) }
    var previewRef by remember { mutableStateOf<Preview?>(null) }
    
    var flashMode by remember { mutableStateOf("AUTO") }
    
    var frameCaptureCallback by remember { mutableStateOf<((ImageProxy) -> Unit)?>(null) }
    val previewView = remember { PreviewView(context).apply { implementationMode = PreviewView.ImplementationMode.COMPATIBLE } }
    
    var isProcessing by remember { mutableStateOf(false) }
    var captureProgress by remember { mutableStateOf(0f) }
    var alignMessage by remember { mutableStateOf("") }
    var cameraIdStr by remember { mutableStateOf("") }

    DisposableEffect(lifecycleOwner) {
        var isDisposed = false
        val analysisExecutor = Executors.newSingleThreadExecutor()
        var imageAnalysisRef: ImageAnalysis? = null
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
        
        cameraProviderFuture.addListener({
            android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                if (isDisposed) return@postDelayed
                
                val cameraProvider = cameraProviderFuture.get()
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
                    cameraProvider.unbindAll()
                    val camera = cameraProvider.bindToLifecycle(
                        lifecycleOwner,
                        CameraSelector.DEFAULT_BACK_CAMERA,
                        preview,
                        imageAnalysis
                    )
                    cameraControlRef = camera.cameraControl
                    camera2ControlRef = Camera2CameraControl.from(camera.cameraControl)
                    cameraIdStr = Camera2CameraInfo.from(camera.cameraInfo).cameraId
                } catch (exc: Exception) {}
            }, 1000)
        }, ContextCompat.getMainExecutor(context))
        
        onDispose {
            isDisposed = true
            if (cameraProviderFuture.isDone) {
                val provider = cameraProviderFuture.get()
                imageAnalysisRef?.clearAnalyzer()
                provider.unbindAll()
            }
            analysisExecutor.shutdown()
        }
    }
    
    val coroutineScope = rememberCoroutineScope()
    
    suspend fun captureFrames(targetList: MutableList<Bitmap>, lockAE: Boolean) {
        isProcessing = true
        targetList.clear()
        captureProgress = 0f
        
        if (lockAE) {
            camera2ControlRef?.let { c2c ->
                val builder = CaptureRequestOptions.Builder()
                builder.setCaptureRequestOption(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_OFF)
                builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON)
                builder.setCaptureRequestOption(CaptureRequest.CONTROL_AWB_MODE, CaptureRequest.CONTROL_AWB_MODE_AUTO)
                c2c.captureRequestOptions = builder.build()
            }
            delay(1000)
            
            // Lock
            camera2ControlRef?.let { c2c ->
                val builder = CaptureRequestOptions.Builder()
                builder.setCaptureRequestOption(CaptureRequest.CONTROL_AE_LOCK, true)
                builder.setCaptureRequestOption(CaptureRequest.CONTROL_AWB_LOCK, true)
                c2c.captureRequestOptions = builder.build()
            }
            delay(200)
        }
        
        var capturedCount = 0
        frameCaptureCallback = { imageProxy ->
            if (capturedCount < 30) {
                val bmp = v4ProxyToBitmap(imageProxy)
                if (bmp != null) {
                    targetList.add(bmp)
                    capturedCount++
                    captureProgress = capturedCount / 30f
                }
            }
        }
        
        while (capturedCount < 30) {
            delay(50)
        }
        frameCaptureCallback = null
        isProcessing = false
    }
    
    Box(modifier = Modifier.fillMaxSize()) {
        androidx.compose.ui.viewinterop.AndroidView(
            factory = { previewView },
            modifier = Modifier.fillMaxSize()
        )
        
        if (currentStep == V4Step.STEP_2_WITH_LENS) {
            Canvas(modifier = Modifier.fillMaxSize()) {
                val w = size.width
                val h = size.height
                val cx = w / 2f
                val cy = h / 2f
                val radius = 100.dp.toPx()
                drawCircle(color = Color.Yellow, radius = radius, center = androidx.compose.ui.geometry.Offset(cx, cy), style = Stroke(width = 4f))
            }
        }
        
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .background(Color(0xBB000000))
                .padding(16.dp)
        ) {
            Text("V4 DIRECT LENS", color = Color.White, fontWeight = FontWeight.Bold)
            Text("Camera ID: $cameraIdStr", color = Color.Gray, fontSize = 12.sp)
            Spacer(modifier = Modifier.height(8.dp))
            
            if (isProcessing) {
                LinearProgressIndicator(progress = { captureProgress }, modifier = Modifier.fillMaxWidth())
                Spacer(modifier = Modifier.height(8.dp))
            }
            
            when (currentStep) {
                V4Step.INIT -> {
                    Button(onClick = { currentStep = V4Step.STEP_1_NO_LENS }, modifier = Modifier.fillMaxWidth()) {
                        Text("START EXPERIMENT")
                    }
                }
                V4Step.STEP_1_NO_LENS -> {
                    Text("STEP 1: REMOVE LENS", color = Color.Yellow, fontWeight = FontWeight.Bold)
                    Text("Point camera at the A4 optical target.", color = Color.White)
                    Spacer(modifier = Modifier.height(8.dp))
                    Button(onClick = {
                        coroutineScope.launch {
                            captureFrames(noLensFrames, lockAE = true)
                            currentStep = V4Step.STEP_2_WITH_LENS
                        }
                    }, modifier = Modifier.fillMaxWidth(), enabled = !isProcessing) {
                        Text("CAPTURE REFERENCE")
                    }
                }
                V4Step.STEP_2_WITH_LENS -> {
                    Text("STEP 2: PLACE LENS DIRECTLY UNDER CAMERA", color = Color.Yellow, fontWeight = FontWeight.Bold)
                    Text("Hold the spectacle lens flat and centered directly under the camera.", color = Color.White)
                    Spacer(modifier = Modifier.height(8.dp))
                    Button(onClick = {
                        coroutineScope.launch {
                            captureFrames(withLensFrames, lockAE = false) // Keep locked state
                            currentStep = V4Step.ANALYZING
                        }
                    }, modifier = Modifier.fillMaxWidth(), enabled = !isProcessing) {
                        Text("CAPTURE LENS")
                    }
                }
                V4Step.ANALYZING -> {
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
                }
                V4Step.COMPLETE -> {
                    Text("MEASUREMENT COMPLETE", color = Color.Green, fontWeight = FontWeight.Bold)
                    Button(onClick = {
                        currentRunIndex = 0
                        runResults.fill(null)
                        overallResult = null
                        currentStep = V4Step.INIT
                    }, modifier = Modifier.fillMaxWidth()) {
                        Text("RESTART")
                    }
                }
            }
        }
    }
    
    if (currentStep == V4Step.COMPLETE && overallResult != null) {
        V4ResultDialog(result = overallResult!!) {
            // Close dialog not needed, it sits on top. We can just wait for restart.
        }
    }
}

@Composable
fun V4ResultDialog(result: V4Result, onDismiss: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xDD000000))
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Column {
            Text("V4 DIRECT LENS RESULT", color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(16.dp))
            
            if (result.success) {
                Text("SPH: ${result.sphDisplay}", color = Color.Cyan, fontSize = 24.sp)
                Text("CYL: ${result.cylDisplay}", color = Color.Cyan, fontSize = 24.sp)
                Text("AXIS: ${result.axisDisplay}", color = Color.Cyan, fontSize = 24.sp)
                
                Spacer(modifier = Modifier.height(16.dp))
                Text("MEAN / STD DEV (REPEATABILITY)", color = Color.Yellow, fontWeight = FontWeight.Bold)
                Text("SPH StdDev: ${String.format("%.4f", result.sphStd)}", color = Color.LightGray)
                Text("CYL StdDev: ${String.format("%.4f", result.cylStd)}", color = Color.LightGray)
                Text("P1 StdDev: ${String.format("%.4f", result.p1Std)}", color = Color.LightGray)
                Text("P2 StdDev: ${String.format("%.4f", result.p2Std)}", color = Color.LightGray)
                
                Spacer(modifier = Modifier.height(16.dp))
                Text("INDIVIDUAL RUNS", color = Color.Yellow, fontWeight = FontWeight.Bold)
                result.allRuns.forEachIndexed { index, run ->
                    Text("RUN ${index + 1}:", color = Color.White, fontWeight = FontWeight.Bold)
                    Text("SPH: ${String.format("%.2f", run.sph)}  CYL: ${String.format("%.2f", run.cyl)}  AXIS: ${String.format("%.0f", run.axis)}", color = Color.LightGray)
                    Text("P1: ${String.format("%.4f", run.p1)}  P2: ${String.format("%.4f", run.p2)}", color = Color.LightGray)
                    Text("Dots: ${run.trackedDots}  RMS: ${String.format("%.2f", run.registrationRms)}", color = Color.LightGray)
                    Spacer(modifier = Modifier.height(8.dp))
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                Text("PRINCIPAL SIGNAL 1: ${String.format("%.4f", result.p1)}", color = Color.LightGray)
                Text("PRINCIPAL SIGNAL 2: ${String.format("%.4f", result.p2)}", color = Color.LightGray)
                Text("ANISOTROPY: ${String.format("%.4f", result.anisotropy)}", color = Color.LightGray)
                Text("ISOTROPIC COMPONENT: ${String.format("%.4f", result.isotropic)}", color = Color.LightGray)
                Text("TRACKED DOTS: ${result.trackedDots}", color = Color.LightGray)
                Text("REGISTRATION RMS: ${String.format("%.2f", result.registrationRms)}", color = Color.LightGray)
                Text("RANSAC INLIERS: ${result.ransacInliers}", color = Color.LightGray)
                Text("FIELD FIT RMS: ${String.format("%.4f", result.fieldFitRms)}", color = Color.LightGray)
                
                Spacer(modifier = Modifier.height(16.dp))
                Text("SCIENTIFIC DEBUG", color = Color.Yellow, fontWeight = FontWeight.Bold)
                Text("Ref Dots: ${result.refDotCount}", color = Color.Gray)
                Text("Lens Dots: ${result.lensDotCount}", color = Color.Gray)
                Text("Mean dx: ${String.format("%.2f", result.meanDx)}", color = Color.Gray)
                Text("Mean dy: ${String.format("%.2f", result.meanDy)}", color = Color.Gray)
                Text("Lambda1: ${String.format("%.4f", result.lambda1)}", color = Color.Gray)
                Text("Lambda2: ${String.format("%.4f", result.lambda2)}", color = Color.Gray)
                
                if (result.visualVectorMap != null) {
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("VISUAL VECTOR MAP (DISPLAY ONLY)", color = Color.White)
                    var mag by remember { mutableStateOf(10f) }
                    Row {
                        Button(onClick = { mag = 1f }) { Text("1x") }
                        Button(onClick = { mag = 5f }) { Text("5x") }
                        Button(onClick = { mag = 10f }) { Text("10x") }
                        Button(onClick = { mag = 20f }) { Text("20x") }
                    }
                    val bmp = V4OpticalAnalyzer.drawVectorMap(result, mag)
                    if (bmp != null) {
                        androidx.compose.foundation.Image(
                            bitmap = bmp.asImageBitmap(),
                            contentDescription = "Vector Map",
                            modifier = Modifier.fillMaxWidth().aspectRatio(bmp.width.toFloat() / bmp.height.toFloat())
                        )
                    }
                }
            } else {
                Text("REPEATABILITY FAILED or QUALITY GATE FAILED", color = Color.Red, fontSize = 20.sp)
                Text("Reason: ${result.errorMessage}", color = Color.White)
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

fun v4ProxyToBitmap(proxy: ImageProxy): Bitmap? {
    val yBuffer = proxy.planes[0].buffer
    val uBuffer = proxy.planes[1].buffer
    val vBuffer = proxy.planes[2].buffer
    
    val ySize = yBuffer.remaining()
    val uSize = uBuffer.remaining()
    val vSize = vBuffer.remaining()
    
    val nv21 = ByteArray(ySize + uSize + vSize)
    yBuffer.get(nv21, 0, ySize)
    vBuffer.get(nv21, ySize, vSize)
    uBuffer.get(nv21, ySize + vSize, uSize)
    
    val yuvImage = android.graphics.YuvImage(nv21, android.graphics.ImageFormat.NV21, proxy.width, proxy.height, null)
    val out = java.io.ByteArrayOutputStream()
    yuvImage.compressToJpeg(android.graphics.Rect(0, 0, proxy.width, proxy.height), 100, out)
    val imageBytes = out.toByteArray()
    return android.graphics.BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
}
