import sys

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    lines = f.readlines()

depth = 0
for i, line in enumerate(lines):
    depth += line.count('{')
    depth -= line.count('}')
    
print(f"Final depth: {depth}")
