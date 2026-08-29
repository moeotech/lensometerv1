import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

pattern = r'var mag by remember \{ mutableStateOf\(10f\) \}\n\s*Row \{\n\s*Button\(onClick = \{ mag = 1f \}\) \{ Text\("1x"\) \}\n\s*Button\(onClick = \{ mag = 5f \}\) \{ Text\("5x"\) \}\n\s*Button\(onClick = \{ mag = 10f \}\) \{ Text\("10x"\) \}\n\s*Button\(onClick = \{ mag = 20f \}\) \{ Text\("20x"\) \}\n\s*\}\n\s*val bmp = V4OpticalAnalyzer\.drawVectorMap\(result, mag\)'

replacement = r"""var mag by remember { mutableStateOf(10f) }
                    var useCorrectedVectors by remember { mutableStateOf(true) }
                    Row {
                        Button(onClick = { mag = 1f }) { Text("1x") }
                        Button(onClick = { mag = 5f }) { Text("5x") }
                        Button(onClick = { mag = 10f }) { Text("10x") }
                        Button(onClick = { mag = 20f }) { Text("20x") }
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Motion Corrected Vectors:", color = Color.White)
                        Switch(checked = useCorrectedVectors, onCheckedChange = { useCorrectedVectors = it })
                    }
                    val bmp = V4OpticalAnalyzer.drawVectorMap(result, mag, useCorrectedVectors)"""

content = re.sub(pattern, replacement, content)

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
