import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r"val t = j00 \+ j11.*?var axisDeg = axisRad \* 180\.0 / PI\n\s*if \(axisDeg < 0\) axisDeg \+= 180\.0"

replacement = """val s00 = j00
            val s11 = j11
            val s01 = 0.5 * (j01 + j10)
            
            val trace = s00 + s11
            val delta = sqrt(((s00 - s11) / 2.0) * ((s00 - s11) / 2.0) + s01 * s01)
            
            var l1 = trace / 2.0 + delta
            var l2 = trace / 2.0 - delta
            
            if (abs(l2) > abs(l1)) {
                val temp = l1; l1 = l2; l2 = temp
            }
            
            val iso = (l1 + l2) / 2.0
            val aniso = abs(l1 - l2)
            
            var axisRad = 0.0
            if (abs(s01) > 1e-6 || abs(s00 - s11) > 1e-6) {
                axisRad = 0.5 * atan2(2.0 * s01, s00 - s11)
            }
            var axisDeg = axisRad * 180.0 / PI
            while (axisDeg < 0.0) axisDeg += 180.0
            while (axisDeg >= 180.0) axisDeg -= 180.0"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)

