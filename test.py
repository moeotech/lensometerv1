import sys

with open('/tmp/trace.txt', 'r') as f:
    text = f.read()
    
open_b = text.count('{')
close_b = text.count('}')

print(f"Open: {open_b}, Close: {close_b}")
