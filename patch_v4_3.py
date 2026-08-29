import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r"""registrationModel = if \(useRigidFallback\) "RIGID_FALLBACK" else "RIGID_ANCHOR",
                registrationRotationDeg = 0\.0, // To be filled later
                registrationTx = 0\.0,
                registrationTy = 0\.0,
                registrationScale = 1\.0,"""
                
replacement = r"""registrationModel = registrationModel,
                registrationRotationDeg = registrationRotationDeg,
                registrationTx = registrationTx,
                registrationTy = registrationTy,
                registrationScale = 1.0,"""

content = re.sub(pattern, replacement, content)

# Now update the calculateRepeatability method
# We replace from `val l1_vals = results.map { it.lambda1 }.sorted()` down to `if (anisotropicMean > 0.02) {`

rep_pattern = r'(val l1_vals = results\.map \{ it\.lambda1 \}\.sorted\(\)\n.*?)(        var axisDisplay = "UNRELIABLE")'

rep_replacement = r"""val lambda1Mean = results.map { it.lambda1 }.average()
        val lambda2Mean = results.map { it.lambda2 }.average()
        val isotropicMean = results.map { it.isotropic }.average()
        val anisotropicMean = results.map { it.anisotropic }.average()

        val lambda1Std = sqrt(results.map { (it.lambda1 - lambda1Mean) * (it.lambda1 - lambda1Mean) }.average())
        val lambda2Std = sqrt(results.map { (it.lambda2 - lambda2Mean) * (it.lambda2 - lambda2Mean) }.average())
        val isotropicStd = sqrt(results.map { (it.isotropic - isotropicMean) * (it.isotropic - isotropicMean) }.average())
        val anisotropicStd = sqrt(results.map { (it.anisotropic - anisotropicMean) * (it.anisotropic - anisotropicMean) }.average())

        val cvThreshold = 0.30
        val minSignal = 0.05
        
        fun checkCv(mean: Double, std: Double, name: String): String? {
            if (Math.abs(mean) > minSignal) {
                val cv = std / Math.abs(mean)
                if (cv > cvThreshold) return "$name CV=${String.format("%.2f", cv)}"
            }
            return null
        }
        
        val fails = listOfNotNull(
            checkCv(lambda1Mean, lambda1Std, "L1"),
            checkCv(lambda2Mean, lambda2Std, "L2"),
            checkCv(isotropicMean, isotropicStd, "ISO"),
            checkCv(anisotropicMean, anisotropicStd, "ANISO")
        )
        
        val l1_vals = results.map { it.lambda1 }.sorted()
        val spreadFails = l1_vals.last() - l1_vals.first() > 0.15
        
        if (fails.isNotEmpty() || spreadFails) {
            val reason = if (fails.isNotEmpty()) fails.joinToString(", ") else "Lambda1 spread > 0.15"
            return@withContext V4Result(success = false, errorMessage = "OPTICAL REPEATABILITY: FAILED ($reason)", allRuns = results, lastRunResult = results.last())
        }

        var axisDisplay = "UNRELIABLE"
"""

content = re.sub(rep_pattern, rep_replacement, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
