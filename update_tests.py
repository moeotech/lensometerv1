import re

with open('app/src/androidTest/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'r') as f:
    content = f.read()

content = content.replace('import org.robolectric.RobolectricTestRunner', 'import androidx.test.ext.junit.runners.AndroidJUnit4')
content = content.replace('import org.robolectric.annotation.Config', '')
content = content.replace('@RunWith(RobolectricTestRunner::class)', '@RunWith(AndroidJUnit4::class)')
content = content.replace('@Config(manifest=Config.NONE)', '')
content = content.replace('nu.pattern.OpenCV.loadShared()', 'org.opencv.android.OpenCVLoader.initLocal()')

with open('app/src/androidTest/java/com/example/analysis/V4OpticalAnalyzerTest.kt', 'w') as f:
    f.write(content)
