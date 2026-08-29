with open('app/src/main/java/com/example/MainActivity.kt', 'r') as f:
    content = f.read()

import_opencv = "import org.opencv.android.OpenCVLoader\nimport android.util.Log\nclass MainActivity"
content = content.replace("class MainActivity", import_opencv)

init_opencv = """  override fun onCreate(savedInstanceState: Bundle?) {
    if (!OpenCVLoader.initDebug()) {
        Log.e("OpenCV", "Unable to load OpenCV!")
    } else {
        Log.d("OpenCV", "OpenCV loaded successfully!")
    }
"""
content = content.replace("  override fun onCreate(savedInstanceState: Bundle?) {", init_opencv)

with open('app/src/main/java/com/example/MainActivity.kt', 'w') as f:
    f.write(content)
