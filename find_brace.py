import sys

def find_brace(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    count = 0
    for i, line in enumerate(lines):
        for char in line:
            if char == '{':
                count += 1
            elif char == '}':
                count -= 1
                if count < 0:
                    print(f"Extra closing brace at line {i+1}")
                    return
    if count > 0:
        print(f"Missing {count} closing braces")

find_brace(sys.argv[1])
