with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    content = f.read()

content = content.replace("                val cx = size.width / 2\n                val cy = size.height / 2\n                val radius", "                val radius")

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.write(content)
