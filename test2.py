import sys

with open('/tmp/trace.txt', 'r') as f:
    text = f.read()

lines = text.split('\n')
open_c = 0
for i, line in enumerate(lines):
    open_c += line.count('{')
    open_c -= line.count('}')
    print(f"Line {i+120}: {open_c}")
