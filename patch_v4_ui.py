import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

ui_pattern = r'Text\("Retained points: \$\{run\.opticalFieldRetainedCount\}", color = Color\.LightGray, fontSize = 12\.sp\)'
ui_replacement = r"""Text("Retained points: ${run.opticalFieldRetainedCount}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Local outliers: ${run.localOutlierRejections}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Crossing rejected: ${run.crossingVectorRejections}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Median local res: ${String.format("%.3f", run.medianLocalResidual)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("MAD local res: ${String.format("%.3f", run.madLocalResidual)}", color = Color.LightGray, fontSize = 12.sp)"""

content = re.sub(ui_pattern, ui_replacement, content)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
