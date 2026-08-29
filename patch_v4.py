import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# 1. Insert estimateStrictRigid right before aggregateFrames
estimate_strict_rigid = """
    private fun estimateStrictRigid(srcPts: List<Point>, dstPts: List<Point>, ransacThresh: Double): Pair<Mat, Mat> {
        val srcMat = MatOfPoint2f().apply { fromList(srcPts) }
        val dstMat = MatOfPoint2f().apply { fromList(dstPts) }
        val mask = Mat()
        val partial = Calib3d.estimateAffinePartial2D(srcMat, dstMat, mask, Calib3d.RANSAC, ransacThresh)
        if (partial.empty()) return Pair(Mat(), mask)

        val maskArray = ByteArray(mask.rows() * mask.cols())
        mask.get(0, 0, maskArray)

        val inlierSrc = mutableListOf<Point>()
        val inlierDst = mutableListOf<Point>()
        for (i in srcPts.indices) {
            if (maskArray[i].toInt() != 0) {
                inlierSrc.add(srcPts[i])
                inlierDst.add(dstPts[i])
            }
        }

        if (inlierSrc.size < 2) return Pair(Mat(), mask)

        var cxSrc = 0.0; var cySrc = 0.0
        var cxDst = 0.0; var cyDst = 0.0
        val N = inlierSrc.size
        for (i in inlierSrc.indices) {
            cxSrc += inlierSrc[i].x; cySrc += inlierSrc[i].y
            cxDst += inlierDst[i].x; cyDst += inlierDst[i].y
        }
        cxSrc /= N; cySrc /= N; cxDst /= N; cyDst /= N

        var h00 = 0.0; var h01 = 0.0; var h10 = 0.0; var h11 = 0.0
        for (i in inlierSrc.indices) {
            val sx = inlierSrc[i].x - cxSrc
            val sy = inlierSrc[i].y - cySrc
            val dx = inlierDst[i].x - cxDst
            val dy = inlierDst[i].y - cyDst
            h00 += sx * dx; h01 += sx * dy
            h10 += sy * dx; h11 += sy * dy
        }

        val H = Mat(2, 2, CvType.CV_64F)
        H.put(0, 0, h00, h01, h10, h11)
        val w = Mat(); val u = Mat(); val vt = Mat()
        Core.SVDecomp(H, w, u, vt)

        val R = Mat(2, 2, CvType.CV_64F)
        Core.gemm(vt.t(), u.t(), 1.0, Mat(), 0.0, R)

        if (Core.determinant(R) < 0) {
            val vtFixed = vt.clone()
            vtFixed.put(1, 0, -vtFixed.get(1, 0)[0], -vtFixed.get(1, 1)[0])
            Core.gemm(vtFixed.t(), u.t(), 1.0, Mat(), 0.0, R)
        }

        val r00 = R.get(0, 0)[0]; val r01 = R.get(0, 1)[0]
        val r10 = R.get(1, 0)[0]; val r11 = R.get(1, 1)[0]

        val tx = cxDst - (r00 * cxSrc + r01 * cySrc)
        val ty = cyDst - (r10 * cxSrc + r11 * cySrc)

        val rigidTransform = Mat(2, 3, CvType.CV_64F)
        rigidTransform.put(0, 0, r00, r01, tx, r10, r11, ty)

        return Pair(rigidTransform, mask)
    }

    private fun aggregateFrames("""

content = content.replace("    private fun aggregateFrames(", estimate_strict_rigid)

# 2. Update aggregateFrames to use estimateStrictRigid
agg_pattern = r"""val transform = Calib3d\.estimateAffinePartial2D\(srcMat, dstMat, mask, Calib3d\.RANSAC, 3\.0\)"""
agg_replacement = r"""val (transform, mask) = estimateStrictRigid(matchedCurr, matchedBase, 3.0)"""
content = re.sub(agg_pattern, agg_replacement, content)
# wait, there's `val mask = Mat()` just before it in the original. Let's fix that.
agg_pattern2 = r"""val mask = Mat\(\)\s*val \(transform, mask\) = estimateStrictRigid\(matchedCurr, matchedBase, 3\.0\)"""
agg_replacement2 = r"""val (transform, mask) = estimateStrictRigid(matchedCurr, matchedBase, 3.0)"""
content = re.sub(agg_pattern2, agg_replacement2, content)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)

