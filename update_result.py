with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Add std dev and run results to V4Result
content = content.replace(
    "val p2: Double = 0.0,",
    "val p2: Double = 0.0,\n    val sphStd: Double = 0.0,\n    val cylStd: Double = 0.0,\n    val p1Std: Double = 0.0,\n    val p2Std: Double = 0.0,\n    val allRuns: List<V4RunResult> = emptyList(),"
)

calc_replace = """        val sphMean = results.map { it.sph }.average()
        val cylMean = results.map { it.cyl }.average()
        val sphStd = sqrt(results.map { (it.sph - sphMean) * (it.sph - sphMean) }.average())
        val cylStd = sqrt(results.map { (it.cyl - cylMean) * (it.cyl - cylMean) }.average())
        val p1Mean = results.map { it.p1 }.average()
        val p2Mean = results.map { it.p2 }.average()
        val p1Std = sqrt(results.map { (it.p1 - p1Mean) * (it.p1 - p1Mean) }.average())
        val p2Std = sqrt(results.map { (it.p2 - p2Mean) * (it.p2 - p2Mean) }.average())"""

content = content.replace(
    """        val sphMean = results.map { it.sph }.average()
        val cylMean = results.map { it.cyl }.average()""",
    calc_replace
)

content = content.replace(
    "val p1Mean = results.map { it.p1 }.average()",
    ""
)
content = content.replace(
    "val p2Mean = results.map { it.p2 }.average()",
    ""
)

ret_replace = """            sphDisplay = "NOT CALIBRATED", // Explicitly uncalibrated per instructions
            cylDisplay = "NOT CALIBRATED",
            axisDisplay = String.format("%.0f", axisMean),
            p1 = p1Mean,
            p2 = p2Mean,
            sphStd = sphStd,
            cylStd = cylStd,
            p1Std = p1Std,
            p2Std = p2Std,
            allRuns = results,"""

content = content.replace(
    """            sphDisplay = "NOT CALIBRATED", // Explicitly uncalibrated per instructions
            cylDisplay = "NOT CALIBRATED",
            axisDisplay = String.format("%.0f", axisMean),
            p1 = p1Mean,
            p2 = p2Mean,""",
    ret_replace
)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
