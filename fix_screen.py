with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

old_img = """                    androidx.compose.foundation.Image(
                        bitmap = V4OpticalAnalyzer.drawVectorMap(result.visualVectorMap!!, mag).asImageBitmap(),
                        contentDescription = "Vector Map",
                        modifier = Modifier.fillMaxWidth().aspectRatio(result.visualVectorMap!!.width.toFloat() / result.visualVectorMap!!.height.toFloat())
                    )"""

new_img = """                    val bmp = V4OpticalAnalyzer.drawVectorMap(result, mag)
                    if (bmp != null) {
                        androidx.compose.foundation.Image(
                            bitmap = bmp.asImageBitmap(),
                            contentDescription = "Vector Map",
                            modifier = Modifier.fillMaxWidth().aspectRatio(bmp.width.toFloat() / bmp.height.toFloat())
                        )
                    }"""

content = content.replace(old_img, new_img)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
