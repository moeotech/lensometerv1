with open('app/src/main/java/com/example/MainActivity.kt', 'r') as f:
    content = f.read()

content = content.replace("import com.example.ui.LensExperimentScreen", "import com.example.ui.LensExperimentScreen\nimport com.example.ui.V4ExperimentScreen")

tabs_replace = """                Button(
                    onClick = { currentTab = 3 },
                    modifier = Modifier.weight(1f),
                    shape = RectangleShape,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (currentTab == 3) Color(0xFFD0BCFF) else Color(0xFF2B2930),
                        contentColor = if (currentTab == 3) Color(0xFF381E72) else Color.White
                    )
                ) { Text("V3 LENS") }
                Button(
                    onClick = { currentTab = 4 },
                    modifier = Modifier.weight(1f),
                    shape = RectangleShape,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (currentTab == 4) Color(0xFFD0BCFF) else Color(0xFF2B2930),
                        contentColor = if (currentTab == 4) Color(0xFF381E72) else Color.White
                    )
                ) { Text("V4") }"""
content = content.replace('                ) { Text("V3 LENS") }', tabs_replace)

content = content.replace("var currentTab by remember { mutableStateOf(3) }", "var currentTab by remember { mutableStateOf(4) }")

when_replace = """              when (currentTab) {
                  1 -> ExperimentScreen()
                  2 -> FocusExperimentScreen()
                  3 -> LensExperimentScreen()
                  4 -> V4ExperimentScreen()
              }"""
content = content.replace("""              when (currentTab) {
                  1 -> ExperimentScreen()
                  2 -> FocusExperimentScreen()
                  3 -> LensExperimentScreen()
              }""", when_replace)

with open('app/src/main/java/com/example/MainActivity.kt', 'w') as f:
    f.write(content)
