import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r'val l1_vals = results\.map \{ it\.lambda1 \}\.sorted\(\)\n\s*val spreadFails = l1_vals\.last\(\) - l1_vals\.first\(\) > 0\.15\n\s*if \(fails\.isNotEmpty\(\) \|\| spreadFails\) \{.*?\n\s*\}'

replacement = r"""
        val l1_vals = results.map { it.lambda1 }.sorted()
        val l2_vals = results.map { it.lambda2 }.sorted()
        val iso_vals = results.map { it.isotropic }.sorted()
        val aniso_vals = results.map { it.anisotropic }.sorted()
        
        val l1Spread = l1_vals.last() - l1_vals.first()
        val l2Spread = l2_vals.last() - l2_vals.first()
        val isoSpread = iso_vals.last() - iso_vals.first()
        val anisoSpread = aniso_vals.last() - aniso_vals.first()
        
        val spreadFails = mutableListOf<String>()
        if (l1Spread > 0.04) spreadFails.add("L1 spread=${String.format("%.3f", l1Spread)}")
        if (l2Spread > 0.03) spreadFails.add("L2 spread=${String.format("%.3f", l2Spread)}")
        if (isoSpread > 0.03) spreadFails.add("ISO spread=${String.format("%.3f", isoSpread)}")
        if (anisoSpread > 0.03) spreadFails.add("ANISO spread=${String.format("%.3f", anisoSpread)}")
        
        if (fails.isNotEmpty() || spreadFails.isNotEmpty()) {
            val reason = (fails + spreadFails).joinToString(", ")
            return@withContext V4Result(success = false, errorMessage = "MEASUREMENT UNSTABLE ($reason)", allRuns = results, lastRunResult = results.last())
        }
"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
