import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Remove the duplicated definitions. They start after `// Optical points to measure:` up to `val transformedLens = dstMeasMat.toList()` and some more.
# Since my replacement had them *before* `// Optical points to measure:`, the ones after are the old ones.

pattern = r'            // Optical points to measure:\n            val ptsToMeasureRef = matchedRef\.toMutableList\(\)\n            val ptsToMeasureLens = matchedLens\.toMutableList\(\)\n            \n            val srcMeasMat = MatOfPoint2f\(\)\n            srcMeasMat\.fromList\(ptsToMeasureLens\)\n            val dstMeasMat = MatOfPoint2f\(\)\n            \n            if \(useRigidFallback\) \{\n                Core\.transform\(srcMeasMat, dstMeasMat, transformMat\)\n            \} else \{\n                Core\.perspectiveTransform\(srcMeasMat, dstMeasMat, transformMat\)\n            \}\n            \n            val transformedLens = dstMeasMat\.toList\(\)\n            \n            if \(!useRigidFallback\) \{\n                var rSum = 0\.0\n                val anchorLensTransformed = MatOfPoint2f\(\)\n                Core\.perspectiveTransform\(srcMat, anchorLensTransformed, transformMat\)\n                val transformedAnchors = anchorLensTransformed\.toList\(\)\n                for \(i in anchorRef\.indices\) \{\n                    if \(maskArray\[i\]\.toInt\(\) != 0\) \{\n                        val dx = transformedAnchors\[i\]\.x - anchorRef\[i\]\.x\n                        val dy = transformedAnchors\[i\]\.y - anchorRef\[i\]\.y\n                        rSum \+= dx \* dx \+ dy \* dy\n                    \}\n                \}\n                registrationRms = sqrt\(rSum / max\(1, inliersCount\)\)\n            \} else \{\n                var rSum = 0\.0\n                for \(i in matchedRef\.indices\) \{\n                    if \(maskArray\[i\]\.toInt\(\) != 0\) \{\n                        val dx = transformedLens\[i\]\.x - matchedRef\[i\]\.x\n                        val dy = transformedLens\[i\]\.y - matchedRef\[i\]\.y\n                        rSum \+= dx \* dx \+ dy \* dy\n                    \}\n                \}\n                registrationRms = sqrt\(rSum / max\(1, inliersCount\)\)\n            \}'

content = content.replace(pattern, "") # wait, re.sub isn't used here, just replace. The pattern has regex syntax though. I'll use re.sub

content = re.sub(pattern, "", content)

# Fix globalScaleAmbiguous = globalScaleAmbiguous in V4RunResult instantiation at the end of analyzePoints
content = re.sub(r'                globalScaleAmbiguous = globalScaleAmbiguous,\n', '', content)
content = re.sub(r'globalScaleAmbiguous = globalScaleAmbiguous,\n', '', content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
