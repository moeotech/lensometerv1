with open('app/src/main/java/com/example/MainActivity.kt', 'r') as f:
    content = f.read()

correct_row = """            Row(modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = { currentTab = 1 },
                    modifier = Modifier.weight(1f),
                    shape = RectangleShape,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (currentTab == 1) Color(0xFFD0BCFF) else Color(0xFF2B2930),
                        contentColor = if (currentTab == 1) Color(0xFF381E72) else Color.White
                    )
                ) { Text("V1.1") }
                
                Button(
                    onClick = { currentTab = 2 },
                    modifier = Modifier.weight(1f),
                    shape = RectangleShape,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (currentTab == 2) Color(0xFFD0BCFF) else Color(0xFF2B2930),
                        contentColor = if (currentTab == 2) Color(0xFF381E72) else Color.White
                    )
                ) { Text("V2") }
                Button(
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
                ) { Text("V4") }
            }"""

import re
content = re.sub(r'            Row\(modifier = Modifier\.fillMaxWidth\(\)\) \{[\s\S]*?            \}', correct_row, content)

with open('app/src/main/java/com/example/MainActivity.kt', 'w') as f:
    f.write(content)

