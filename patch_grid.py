import os

path = "app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt"
with open(path, "r") as f:
    text = f.read()

replacement = """    private fun assignGridTopology(points: List<Point>, spacing: Double, rejections: MutableMap<String, Int> = mutableMapOf()): Map<Pair<Int, Int>, Point> {
        if (points.isEmpty()) return emptyMap()
        
        val angles = mutableListOf<Double>()
        for (i in points.indices) {
            for (j in i + 1 until points.size) {
                val p1 = points[i]
                val p2 = points[j]
                val dx = p2.x - p1.x
                val dy = p2.y - p1.y
                val dist = hypot(dx, dy)
                if (dist > spacing * 0.5 && dist < spacing * 1.5) {
                    var a = Math.atan2(dy, dx)
                    while (a < 0) a += Math.PI / 2.0
                    while (a >= Math.PI / 2.0) a -= Math.PI / 2.0
                    angles.add(a)
                }
            }
        }
        
        val medianAngle = if (angles.isNotEmpty()) {
            angles.sort()
            angles[angles.size / 2]
        } else 0.0
        
        val cosA = Math.cos(-medianAngle)
        val sinA = Math.sin(-medianAngle)
        
        val cx = points.map { it.x }.average()
        val cy = points.map { it.y }.average()
        
        val grid = mutableMapOf<Pair<Int, Int>, Point>()
        
        var assigned = 0
        var ambiguous = 0
        var collisions = 0
        
        for (p in points) {
            val tx = p.x - cx
            val ty = p.y - cy
            val rx = tx * cosA - ty * sinA
            val ry = tx * sinA + ty * cosA
            
            val col = (rx / spacing).roundToInt()
            val row = (ry / spacing).roundToInt()
            
            val coord = Pair(row, col)
            if (grid.containsKey(coord)) {
                collisions++
                val existing = grid[coord]!!
                
                val idealRx = col * spacing
                val idealRy = row * spacing
                
                val extTx = existing.x - cx
                val extTy = existing.y - cy
                val erx = extTx * cosA - extTy * sinA
                val ery = extTx * sinA + extTy * cosA
                
                val eDistSq = (erx - idealRx)*(erx - idealRx) + (ery - idealRy)*(ery - idealRy)
                val pDistSq = (rx - idealRx)*(rx - idealRx) + (ry - idealRy)*(ry - idealRy)
                
                if (pDistSq < eDistSq) {
                    grid[coord] = p
                    ambiguous++
                } else {
                    ambiguous++
                }
            } else {
                grid[coord] = p
                assigned++
            }
        }
        rejections["gridAssigned"] = grid.size
        rejections["gridAmbiguous"] = ambiguous
        rejections["gridCollisions"] = collisions
        return grid
    }"""

import re
start_str = "    private fun assignGridTopology(points: List<Point>, spacing: Double): Map<Pair<Int, Int>, Point> {"
end_str = "        return grid\n    }"
start_idx = text.find(start_str)
end_idx = text.find(end_str, start_idx) + len(end_str)

target = text[start_idx:end_idx]
text = text.replace(target, replacement)

# replace call sites
text = text.replace("val gridMap = assignGridTopology(baseRefPoints, spacing)", "val gridMap = assignGridTopology(baseRefPoints, spacing, rejections)")

with open(path, "w") as f:
    f.write(text)
