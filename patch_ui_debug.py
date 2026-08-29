import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

run_search = """                    Text("Dots: ${run.trackedDots} Reg RMS: ${String.format("%.2f", run.registrationRms)}", color = Color.LightGray)"""
run_replacement = """                    Text("Debug metrics:", color = Color.Gray, fontSize = 12.sp)
                    Text("- Detected dots: Ref ${run.refDotCount} / Lens ${run.lensDotCount}", color = Color.Gray, fontSize = 12.sp)
                    Text("- Matches: ${run.candidateMatches} cand, ${run.acceptedMatches} acc, ${run.rejectedMatches} rej", color = Color.Gray, fontSize = 12.sp)
                    Text("- Matrix: rank ${run.matrixRank}, cond ${String.format("%.1f", run.conditionNumber)}, status ${run.degeneracyStatus}", color = Color.Gray, fontSize = 12.sp)
                    Text("- RMS: reg ${String.format("%.3f", run.registrationRms)}, fit ${String.format("%.3f", run.fieldFitRms)}", color = Color.Gray, fontSize = 12.sp)
                    Text("- Frames acc: ${run.framesAccepted}", color = Color.Gray, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(4.dp))"""

content = content.replace(run_search, run_search + "\n" + run_replacement)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
