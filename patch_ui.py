import os
path = "app/src/main/java/com/example/ui/V4ExperimentScreen.kt"
with open(path, "r") as f:
    text = f.read()

replacement = """
                    Text("TOPOLOGY TELEMETRY", color = Color.Yellow, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text("Ref Dots: ${run.refDotCount} | Lens Dots: ${run.lensDotCount}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Grid Assigned: ${run.matchRejections["gridAssigned"] ?: 0} | Grid Ambiguous: ${run.matchRejections["gridAmbiguous"] ?: 0}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Seed Mutual Matches: ${run.matchRejections["seedMutualMatches"] ?: 0}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Neighbor-expanded: ${run.matchRejections["neighborExpandedMatches"] ?: 0}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Affine-expanded: ${run.matchRejections["affineExpandedMatches"] ?: 0}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Final 1-to-1 matches: ${run.matchRejections["finalMatches"] ?: run.topologyMatchCount}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Quadrants: ${listOf(run.matchRejections["Quad1_Matches"] ?: 0, run.matchRejections["Quad2_Matches"] ?: 0, run.matchRejections["Quad3_Matches"] ?: 0, run.matchRejections["Quad4_Matches"] ?: 0).count { it > 0 }}", color = Color.LightGray, fontSize = 12.sp)
                    
                    val coverageStr = if (run.refDotCount > 0) String.format("%.1f", ((run.matchRejections["finalMatches"] ?: run.topologyMatchCount).toDouble() / run.refDotCount) * 100) + "%" else "0%"
                    Text("Spatial Coverage: $coverageStr", color = Color.LightGray, fontSize = 12.sp)
                    
                    Text("REJECTIONS:", color = Color.LightGray, fontSize = 12.sp)
                    Text("seed_distance: ${run.matchRejections["seed_distance"] ?: 0} | non_mutual: ${run.matchRejections["non_mutual"] ?: 0}", color = Color.Red, fontSize = 12.sp)
                    Text("topology_collision: ${run.matchRejections["gridCollisions"] ?: 0}", color = Color.Red, fontSize = 12.sp)
                    Text("assignment_conflict: ${run.matchRejections["assignment_conflict"] ?: 0}", color = Color.Red, fontSize = 12.sp)
                    Text("unmatched_lens: ${run.matchRejections["unmatched_lens_dots"] ?: 0} | unmatched_ref: ${run.matchRejections["topology_rejection"] ?: 0}", color = Color.Red, fontSize = 12.sp)
                    
                    Text("Q1: ${run.matchRejections["Quad1_Matches"] ?: 0} Q2: ${run.matchRejections["Quad2_Matches"] ?: 0} Q3: ${run.matchRejections["Quad3_Matches"] ?: 0} Q4: ${run.matchRejections["Quad4_Matches"] ?: 0}", color = Color.LightGray, fontSize = 12.sp)
"""

start_str = """
                    Text("TOPOLOGY", color = Color.Yellow, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text("Matched: ${run.topologyMatchCount}", color = Color.LightGray, fontSize = 12.sp)
                    Text("Q1: ${run.matchRejections["Quad1_Matches"] ?: 0} Q2: ${run.matchRejections["Quad2_Matches"] ?: 0} Q3: ${run.matchRejections["Quad3_Matches"] ?: 0} Q4: ${run.matchRejections["Quad4_Matches"] ?: 0}", color = Color.LightGray, fontSize = 12.sp)
"""

text = text.replace(start_str, replacement)

with open(path, "w") as f:
    f.write(text)
