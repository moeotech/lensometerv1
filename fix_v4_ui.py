with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

import re
old_text = r'                Text\("SPH: \$\{result\.sphDisplay\}".*?Text\("Lambda2: \$\{String\.format\("%.4f", result\.lambda2\)\}", color = Color\.Gray\)'
new_text = """                Text("SPH: ${result.sphDisplay}", color = Color.Cyan, fontSize = 24.sp)
                Text("CYL: ${result.cylDisplay}", color = Color.Cyan, fontSize = 24.sp)
                Text("AXIS SIGNAL: ${result.axisDisplay}°", color = Color.Cyan, fontSize = 24.sp)
                
                if (result.globalScaleAmbiguous) {
                    Text("GLOBAL_SCALE_AMBIGUOUS", color = Color.Red, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                Text("RAW OPTICAL FIELD", color = Color.Yellow, fontWeight = FontWeight.Bold)
                Text("Lambda 1: ${String.format("%.6f", result.lambda1)}", color = Color.LightGray)
                Text("Lambda 2: ${String.format("%.6f", result.lambda2)}", color = Color.LightGray)
                Text("Isotropic: ${String.format("%.6f", result.isotropic)}", color = Color.LightGray)
                Text("Anisotropic: ${String.format("%.6f", result.anisotropic)}", color = Color.LightGray)
                Text("Axis: ${result.axisDisplay}°", color = Color.LightGray)
                Text("Matched dots: ${result.trackedDots}", color = Color.LightGray)
                Text("Stable dots: ${result.refDotCount}", color = Color.LightGray)
                
                val framesAcc = result.allRuns.sumOf { it.framesAccepted }
                Text("Frames accepted: $framesAcc", color = Color.LightGray)
                Text("Registration RMS: ${String.format("%.3f", result.registrationRms)}", color = Color.LightGray)
                Text("Field-fit RMS: ${String.format("%.3f", result.fieldFitRms)}", color = Color.LightGray)

                Spacer(modifier = Modifier.height(16.dp))
                Text("MEAN / STD DEV (REPEATABILITY)", color = Color.Yellow, fontWeight = FontWeight.Bold)
                Text("Lambda 1 StdDev: ${String.format("%.6f", result.lambda1Std)}", color = Color.LightGray)
                Text("Lambda 2 StdDev: ${String.format("%.6f", result.lambda2Std)}", color = Color.LightGray)
                Text("Isotropic StdDev: ${String.format("%.6f", result.isotropicStd)}", color = Color.LightGray)
                Text("Anisotropic StdDev: ${String.format("%.6f", result.anisotropicStd)}", color = Color.LightGray)
                
                Spacer(modifier = Modifier.height(16.dp))
                Text("INDIVIDUAL RUNS", color = Color.Yellow, fontWeight = FontWeight.Bold)
                result.allRuns.forEachIndexed { index, run ->
                    Text("RUN ${index + 1}:", color = Color.White, fontWeight = FontWeight.Bold)
                    Text("L1: ${String.format("%.4f", run.lambda1)} L2: ${String.format("%.4f", run.lambda2)} Iso: ${String.format("%.4f", run.isotropic)}", color = Color.LightGray)
                    Text("Dots: ${run.trackedDots} Reg RMS: ${String.format("%.2f", run.registrationRms)}", color = Color.LightGray)
                    Spacer(modifier = Modifier.height(8.dp))
                }"""

content = re.sub(old_text, new_text, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
