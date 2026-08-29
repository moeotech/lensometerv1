with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

content = content.replace(
    "val sphStd = sqrt(results.map { (it.sph - sphMean) * (it.sph - sphMean) }.average())",
    "val p1Mean = results.map { it.p1 }.average()\n        val p2Mean = results.map { it.p2 }.average()\n        val sphStd = sqrt(results.map { (it.sph - sphMean) * (it.sph - sphMean) }.average())"
)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
