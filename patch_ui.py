import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

res_old = """                if (result.globalScaleAmbiguous) {
                    Text("GLOBAL_SCALE_AMBIGUOUS", color = Color.Red, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                }"""

res_new = """                if (result.globalScaleAmbiguous) {
                    Text("GLOBAL_SCALE_AMBIGUOUS", color = Color.Red, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                    Text("SPHERE SIGNAL MAY BE SUPPRESSED BY REGISTRATION", color = Color.Red, fontSize = 12.sp)
                }"""

content = content.replace(res_old, res_new)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)

