import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

res_old = """                    Text("RUN ${index + 1}:", color = Color.White, fontWeight = FontWeight.Bold)
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
                    Text("- Frames acc: ${run.framesAccepted}", color = Color.Gray, fontSize = 12.sp)"""

res_new = """                    Text("RUN ${index + 1}:", color = Color.White, fontWeight = FontWeight.Bold)
                    Text("L1: ${String.format("%.4f", run.lambda1)} L2: ${String.format("%.4f", run.lambda2)} Iso: ${String.format("%.4f", run.isotropic)}", color = Color.LightGray)
                    
                    Text("TOPOLOGY", color = Color.Yellow, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text("Matched: ${run.topologyMatchCount}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Q1: ${run.matchRejections["Quad1_Matches"] ?: 0} Q2: ${run.matchRejections["Quad2_Matches"] ?: 0} Q3: ${run.matchRejections["Quad3_Matches"] ?: 0} Q4: ${run.matchRejections["Quad4_Matches"] ?: 0}", color = Color.LightGray, fontSize = 12.sp)
                    
                    Text("REGISTRATION", color = Color.Yellow, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text("Features: ${run.registrationFeatureCount}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Inliers: ${run.registrationInliers}", color = Color.LightGray, fontSize = 12.sp)
                    Text("RMS: ${String.format("%.3f", run.registrationRms)}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Scale ambiguous: ${if (run.globalScaleAmbiguous) "YES" else "NO"}", color = Color.LightGray, fontSize = 12.sp)
                    
                    Text("OPTICAL FIELD", color = Color.Yellow, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text("Input points: ${run.opticalFieldInputCount}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Retained points: ${run.opticalFieldRetainedCount}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Quadrants: ${run.quadrantCoverage}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Coverage: ${String.format("%.1f", run.spatialCoveragePct)}%", color = Color.LightGray, fontSize = 12.sp)
                    Text("Fit RMS: ${String.format("%.3f", run.fieldFitRms)}", color = Color.LightGray, fontSize = 12.sp)
                    
                    if (run.matchRejections.isNotEmpty()) {
                        Text("Other rejections: ${run.matchRejections.entries.filter { !it.key.startsWith("Quad") }.joinToString { "${it.key}: ${it.value}" }}", color = Color.Gray, fontSize = 12.sp)
                    }"""

content = content.replace(res_old, res_new)
with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)

