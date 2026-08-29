with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'r') as f:
    content = f.read()

# Fix the end of detectLensEllipse
content = content.replace("            }\n        }\n    }\n    mat.release();", "            }\n        }\n    mat.release();")

# We need to make sure LensExperimentScreen is properly closed
# Let's count the braces
open_braces = content.count('{')
close_braces = content.count('}')

print(f"Open: {open_braces}, Close: {close_braces}")
if open_braces > close_braces:
    # Add braces before proxyToBitmap
    parts = content.split("fun proxyToBitmap(image: ImageProxy): Bitmap? {")
    if len(parts) == 2:
        missing = open_braces - close_braces
        braces = "}\n" * missing
        content = parts[0] + braces + "fun proxyToBitmap(image: ImageProxy): Bitmap? {" + parts[1]

with open('app/src/main/java/com/example/ui/LensExperimentScreen.kt', 'w') as f:
    f.write(content)

