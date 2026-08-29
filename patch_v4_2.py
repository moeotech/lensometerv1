import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Replace the registration block in analyzePoints
pattern = r'(var registrationRms = 0\.0\s*var inliersCount = 0\s*)(val useRigidFallback = anchorRef\.size < 15.*?)(            // Optical points to measure:)'

replacement = r"""var registrationRms = 0.0
            var inliersCount = 0
            
            val useRigidFallback = anchorRef.size < 4
            
            val regSrc: List<Point>
            val regDst: List<Point>
            if (useRigidFallback) {
                regSrc = matchedLens
                regDst = matchedRef
            } else {
                regSrc = anchorLens
                regDst = anchorRef
            }
            
            val ransacThresh = if (useRigidFallback) max(15.0, spacing * 0.8) else max(5.0, spacing * 0.4)
            
            if (regSrc.size < 4) {
                return V4RunResult(success = false, errorMessage = "REGISTRATION UNSTABLE (Not enough points)", candidateMatches = matchedRef.size, matchRejections = rejections)
            }
            
            val (transformMat, mask) = estimateStrictRigid(regSrc, regDst, ransacThresh)
            
            if (transformMat.empty()) {
                rejections["registration_inconsistency"] = rejections.getOrDefault("registration_inconsistency", 0) + matchedRef.size
                return V4RunResult(success = false, errorMessage = "Registration failed", candidateMatches = matchedRef.size, matchRejections = rejections)
            }
            
            val r00 = transformMat.get(0, 0)[0]
            val r10 = transformMat.get(1, 0)[0]
            val registrationRotationDeg = atan2(r10, r00) * 180.0 / Math.PI
            val registrationTx = transformMat.get(0, 2)[0]
            val registrationTy = transformMat.get(1, 2)[0]
            val registrationModel = if (useRigidFallback) "RIGID_FALLBACK" else "RIGID_ANCHOR"
            
            val maskArray = ByteArray(mask.rows() * mask.cols())
            mask.get(0, 0, maskArray)
            inliersCount = maskArray.count { it.toInt() != 0 }
            
            val ptsToMeasureRef = matchedRef.toMutableList()
            val ptsToMeasureLens = matchedLens.toMutableList()
            
            val srcMeasMat = MatOfPoint2f()
            srcMeasMat.fromList(ptsToMeasureLens)
            val dstMeasMat = MatOfPoint2f()
            
            Core.transform(srcMeasMat, dstMeasMat, transformMat)
            val transformedLens = dstMeasMat.toList()
            
            if (!useRigidFallback) {
                var rSum = 0.0
                val anchorLensMat = MatOfPoint2f().apply { fromList(anchorLens) }
                val anchorLensTransformed = MatOfPoint2f()
                Core.transform(anchorLensMat, anchorLensTransformed, transformMat)
                val transformedAnchors = anchorLensTransformed.toList()
                for (i in anchorRef.indices) {
                    if (maskArray[i].toInt() != 0) {
                        val dx = transformedAnchors[i].x - anchorRef[i].x
                        val dy = transformedAnchors[i].y - anchorRef[i].y
                        rSum += dx * dx + dy * dy
                    }
                }
                registrationRms = sqrt(rSum / max(1, inliersCount))
            } else {
                var rSum = 0.0
                for (i in matchedRef.indices) {
                    if (maskArray[i].toInt() != 0) {
                        val dx = transformedLens[i].x - matchedRef[i].x
                        val dy = transformedLens[i].y - matchedRef[i].y
                        rSum += dx * dx + dy * dy
                    }
                }
                registrationRms = sqrt(rSum / max(1, inliersCount))
            }
            
            // Optical points to measure:"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
