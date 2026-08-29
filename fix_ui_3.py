import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

old_res = r"""Text\("Scale ambiguous: \$\{if \(run\.globalScaleAmbiguous\) "YES" else "NO"\}", color = Color\.LightGray, fontSize = 12\.sp\)"""

new_res = r"""Text("Model: ${run.registrationModel}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Scale: ${String.format("%.4f", run.registrationScale)}", color = Color.LightGray, fontSize = 12.sp)"""

content = re.sub(old_res, new_res, content)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
