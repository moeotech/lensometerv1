with open('app/src/main/java/com/example/MainActivity.kt', 'r') as f:
    content = f.read()

new_init = """    try {
        System.loadLibrary("opencv_java4")
        Log.d("OpenCV", "OpenCV loaded successfully via System.loadLibrary")
    } catch (e: UnsatisfiedLinkError) {
        Log.e("OpenCV", "Unable to load OpenCV: ${e.message}")
    }"""

content = content.replace("""    if (!OpenCVLoader.initDebug()) {
        Log.e("OpenCV", "Unable to load OpenCV!")
    } else {
        Log.d("OpenCV", "OpenCV loaded successfully!")
    }""", new_init)

with open('app/src/main/java/com/example/MainActivity.kt', 'w') as f:
    f.write(content)
