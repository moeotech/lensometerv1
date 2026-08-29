import re

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'r') as f:
    content = f.read()

if "import androidx.compose.material3.Switch" not in content:
    content = content.replace('import androidx.compose.material3.Text', 'import androidx.compose.material3.Text\nimport androidx.compose.material3.Switch')

with open('app/src/main/java/com/example/ui/V4ExperimentScreen.kt', 'w') as f:
    f.write(content)
