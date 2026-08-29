with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    content = f.read()

content = content.replace("}\n}\n}\n}\n}\n}\nfun proxyToBitmap", "}\nfun proxyToBitmap")

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.write(content)
