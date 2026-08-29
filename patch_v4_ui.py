import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

pattern = r'Text\("MAD local res: \$\{String\.format\("%.3f", run\.madLocalResidual\)\}", color = Color\.LightGray, fontSize = 12\.sp\)'
replacement = r"""Text("MAD local res: ${String.format("%.3f", run.madLocalResidual)}", color = Color.LightGray, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("Disp Median: ${String.format("%.2f", run.dispMedian)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Disp MAD: ${String.format("%.2f", run.dispMAD)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Disp P90: ${String.format("%.2f", run.dispP90)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Disp Max: ${String.format("%.2f", run.dispMax)}", color = Color.LightGray, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(4.dp))"""

content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
