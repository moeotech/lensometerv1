import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

content = re.sub(r',\s*globalScaleAmbiguous = results.any \{ it.globalScaleAmbiguous \}', '', content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

# there is still a result.globalScaleAmbiguous reference? Let's check V4ExperimentScreen
