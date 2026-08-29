import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

pattern = r'Text\("Disp Median: \$\{String\.format\("%.2f", run\.dispMedian\)\}", color = Color\.LightGray, fontSize = 12\.sp\)\n\s*Text\("Disp MAD: \$\{String\.format\("%.2f", run\.dispMAD\)\}", color = Color\.LightGray, fontSize = 12\.sp\)\n\s*Text\("Disp P90: \$\{String\.format\("%.2f", run\.dispP90\)\}", color = Color\.LightGray, fontSize = 12\.sp\)\n\s*Text\("Disp Max: \$\{String\.format\("%.2f", run\.dispMax\)\}", color = Color\.LightGray, fontSize = 12\.sp\)'

replacement = r"""Text("Raw Disp Median: ${String.format("%.2f", run.dispMedian)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Raw Disp MAD: ${String.format("%.2f", run.dispMAD)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Raw Disp P90: ${String.format("%.2f", run.dispP90)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Raw Disp Max: ${String.format("%.2f", run.dispMax)}", color = Color.LightGray, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("Global Motion X: ${String.format("%.2f", run.globalMotionX)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Global Motion Y: ${String.format("%.2f", run.globalMotionY)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Global Motion Mag: ${String.format("%.2f", run.globalMotionMagnitude)}", color = Color.LightGray, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("Corrected Disp Median: ${String.format("%.2f", run.correctedDispMedian)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Corrected Disp MAD: ${String.format("%.2f", run.correctedDispMAD)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Corrected Disp P90: ${String.format("%.2f", run.correctedDispP90)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Corrected Disp Max: ${String.format("%.2f", run.correctedDispMax)}", color = Color.LightGray, fontSize = 12.sp)"""

content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
