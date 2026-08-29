import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

old_res = r"""                if \(result\.globalScaleAmbiguous\) \{
                    Text\("GLOBAL_SCALE_AMBIGUOUS", color = Color\.Red, fontWeight = FontWeight\.Bold, fontSize = 20\.sp\)
                    Text\("SPHERE SIGNAL MAY BE SUPPRESSED BY REGISTRATION", color = Color\.Red, fontSize = 12\.sp\)
                \}"""

new_res = r"""                Spacer(modifier = Modifier.height(16.dp))
                Text("REGISTRATION DIAGNOSTICS", color = Color.Yellow, fontWeight = FontWeight.Bold)
                Text("Model: ${result.lastRunResult?.registrationModel ?: "NONE"}", color = Color.LightGray)
                Text("Scale: ${String.format("%.6f", result.lastRunResult?.registrationScale ?: 1.0)}", color = Color.LightGray)
                Text("Rot: ${String.format("%.2f", result.lastRunResult?.registrationRotationDeg ?: 0.0)}°", color = Color.LightGray)
                Text("Tx: ${String.format("%.1f", result.lastRunResult?.registrationTx ?: 0.0)}", color = Color.LightGray)
                Text("Ty: ${String.format("%.1f", result.lastRunResult?.registrationTy ?: 0.0)}", color = Color.LightGray)
                Text("Inliers: ${result.lastRunResult?.registrationInliers ?: 0} / ${result.lastRunResult?.registrationFeatureCount ?: 0}", color = Color.LightGray)
"""

content = re.sub(old_res, new_res, content)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
