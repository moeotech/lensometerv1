import sys

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    lines = f.readlines()

depth = 0
for i, line in enumerate(lines):
    depth += line.count('{')
    depth -= line.count('}')
    if 280 < i < 330:
        print(f"{i+1:3d} | {depth:2d} | {line.rstrip()}")
