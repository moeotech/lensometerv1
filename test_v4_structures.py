import re
with open('/tmp/dev/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

print("Found V4RunResult:", 'V4RunResult' in content)
print("Found V4Result:", 'V4Result' in content)
