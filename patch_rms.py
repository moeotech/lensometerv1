import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

pattern = r'val dx = retainedPairs\[i\]\.displacement\.x\n\s*val dy = retainedPairs\[i\]\.displacement\.y'
replacement = r"""val dx = retainedPairs[i].correctedDisplacement.x
                    val dy = retainedPairs[i].correctedDisplacement.y"""
content = re.sub(pattern, replacement, content)

pattern2 = r'sumDx \+= retainedPairs\[i\]\.displacement\.x\n\s*sumDy \+= retainedPairs\[i\]\.displacement\.y'
replacement2 = r"""sumDx += retainedPairs[i].correctedDisplacement.x
                sumDy += retainedPairs[i].correctedDisplacement.y"""
content = re.sub(pattern2, replacement2, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
