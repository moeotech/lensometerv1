with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

ui_replace = """                Text("SPH: ${result.sphDisplay}", color = Color.Cyan, fontSize = 24.sp)
                Text("CYL: ${result.cylDisplay}", color = Color.Cyan, fontSize = 24.sp)
                Text("AXIS: ${result.axisDisplay}", color = Color.Cyan, fontSize = 24.sp)
                
                Spacer(modifier = Modifier.height(16.dp))
                Text("MEAN / STD DEV (REPEATABILITY)", color = Color.Yellow, fontWeight = FontWeight.Bold)
                Text("SPH StdDev: ${String.format("%.4f", result.sphStd)}", color = Color.LightGray)
                Text("CYL StdDev: ${String.format("%.4f", result.cylStd)}", color = Color.LightGray)
                Text("P1 StdDev: ${String.format("%.4f", result.p1Std)}", color = Color.LightGray)
                Text("P2 StdDev: ${String.format("%.4f", result.p2Std)}", color = Color.LightGray)
                
                Spacer(modifier = Modifier.height(16.dp))
                Text("INDIVIDUAL RUNS", color = Color.Yellow, fontWeight = FontWeight.Bold)
                result.allRuns.forEachIndexed { index, run ->
                    Text("RUN ${index + 1}:", color = Color.White, fontWeight = FontWeight.Bold)
                    Text("SPH: ${String.format("%.2f", run.sph)}  CYL: ${String.format("%.2f", run.cyl)}  AXIS: ${String.format("%.0f", run.axis)}", color = Color.LightGray)
                    Text("P1: ${String.format("%.4f", run.p1)}  P2: ${String.format("%.4f", run.p2)}", color = Color.LightGray)
                    Text("Dots: ${run.trackedDots}  RMS: ${String.format("%.2f", run.registrationRms)}", color = Color.LightGray)
                    Spacer(modifier = Modifier.height(8.dp))
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                Text("PRINCIPAL SIGNAL 1: ${String.format("%.4f", result.p1)}", color = Color.LightGray)"""

content = content.replace(
    """                Text("SPH: ${result.sphDisplay}", color = Color.Cyan, fontSize = 24.sp)
                Text("CYL: ${result.cylDisplay}", color = Color.Cyan, fontSize = 24.sp)
                Text("AXIS: ${result.axisDisplay}", color = Color.Cyan, fontSize = 24.sp)
                
                Spacer(modifier = Modifier.height(16.dp))
                Text("PRINCIPAL SIGNAL 1: ${String.format("%.4f", result.p1)}", color = Color.LightGray)""",
    ui_replace
)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
