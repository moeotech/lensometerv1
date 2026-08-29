import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

# I want to add new outputs to individual runs
new_run_info = """
                    Text("RUN ${index + 1}:", color = Color.White, fontWeight = FontWeight.Bold)
                    Text("L1: ${String.format("%.4f", run.lambda1)} L2: ${String.format("%.4f", run.lambda2)} Iso: ${String.format("%.4f", run.isotropic)}", color = Color.LightGray)
                    Text("Dots: ${run.trackedDots} Reg RMS: ${String.format("%.2f", run.registrationRms)}", color = Color.LightGray)
                    Text("Debug metrics:", color = Color.Gray, fontSize = 12.sp)
                    Text("- Detected dots: Ref ${run.refDotCount} / Lens ${run.lensDotCount}", color = Color.Gray, fontSize = 12.sp)
                    Text("- Matches: ${run.candidateMatches} cand, ${run.acceptedMatches} acc", color = Color.Gray, fontSize = 12.sp)
                    if (run.matchRejections.isNotEmpty()) {
                        Text("- Rejections: ${run.matchRejections.entries.joinToString { "${it.key}: ${it.value}" }}", color = Color.Gray, fontSize = 12.sp)
                    }
                    Text("- Spatial coverage: ${String.format("%.1f", run.spatialCoveragePct)}%, Quads: ${run.quadrantCoverage}", color = Color.Gray, fontSize = 12.sp)
                    Text("- Temporal: ${run.temporalTrackCount} tracks, ${run.stableTrackCount} stable, ${String.format("%.1f", run.medianTrackLifetime * 100.0)}% life", color = Color.Gray, fontSize = 12.sp)
                    Text("- Matrix: rank ${run.matrixRank}, cond ${String.format("%.1f", run.conditionNumber)}, status ${run.degeneracyStatus}", color = Color.Gray, fontSize = 12.sp)
                    Text("- RMS: reg ${String.format("%.3f", run.registrationRms)}, fit ${String.format("%.3f", run.fieldFitRms)}", color = Color.Gray, fontSize = 12.sp)
                    Text("- Frames acc: ${run.framesAccepted}", color = Color.Gray, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    if (!run.success) {
                        Text("FAILURE: ${run.errorMessage}", color = Color.Red, fontSize = 12.sp)
                    }
"""

old_run_info_pattern = r'Text\("RUN \$\{index \+ 1\}:".*?Spacer\(modifier = Modifier\.height\(8\.dp\)\)'

content = re.sub(old_run_info_pattern, new_run_info.strip(), content, flags=re.DOTALL)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
