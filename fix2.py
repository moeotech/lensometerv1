with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "analysisExecutor.shutdown()" in line:
        new_lines.append(line)
        new_lines.append("        }\n")
        new_lines.append("    }\n")
        continue
    new_lines.append(line)

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.writelines(new_lines)

