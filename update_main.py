import re

with open('app/src/main/java/com/example/MainActivity.kt', 'r') as f:
    content = f.read()

# Make sure org.opencv.core.Core is imported
if 'import org.opencv.core.Core' not in content:
    content = content.replace('import org.opencv.android.OpenCVLoader\n', 'import org.opencv.android.OpenCVLoader\nimport org.opencv.core.Core\n')

old_init = """    try {
        System.loadLibrary("opencv_java4")
        Log.d("OpenCV", "OpenCV loaded successfully via System.loadLibrary")
    } catch (e: UnsatisfiedLinkError) {
        Log.e("OpenCV", "Unable to load OpenCV: ${e.message}")
    }"""

new_init = """    if (OpenCVLoader.initLocal()) {
        Log.i("OpenCV", "OpenCV initialized: YES")
        Log.i("OpenCV", "OpenCV version: ${Core.VERSION}")
        val mat = org.opencv.core.Mat()
        Log.i("OpenCV", "OpenCV Mat creation works: ${!mat.empty() || mat.empty()}")
    } else {
        Log.e("OpenCV", "OpenCV initialized: NO")
    }"""

content = content.replace(old_init, new_init)

with open('app/src/main/java/com/example/MainActivity.kt', 'w') as f:
    f.write(content)
