package com.example.model

data class LensMeasurementResult(
    val sph: Double,
    val cyl: Double,
    val axis: Double,
    val calibrated: Boolean,
    val confidence: String,
    val trackedPoints: Int,
    val meanDx: Double,
    val meanDy: Double,
    val maxDisplacement: Double,
    val p1: Double,
    val p1Angle: Double,
    val p2: Double,
    val p2Angle: Double,
    val directionalSignals: Map<Int, Double>
)
