with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Let's search for "suspend fun analyze("
parts = content.split("suspend fun analyze(noLensFrames: List<Bitmap>, withLensFrames: List<Bitmap>): V4RunResult = withContext(Dispatchers.Default) {")

if len(parts) > 2:
    print(f"Found {len(parts)} parts!")
    # the correct file should just be parts[0] + "suspend fun analyze(noLensFrames: List<Bitmap>, withLensFrames: List<Bitmap>): V4RunResult = withContext(Dispatchers.Default) {" + parts[-1]
    
    # Wait, parts[-1] contains `calculateRepeatability` and `drawVectorMap`.
    # Let's verify parts[-1] doesn't have duplicates.
    sub_parts = parts[-1].split("fun analyzePoints(")
    if len(sub_parts) > 2:
        print(f"Found {len(sub_parts)} analyzePoints parts!")
        # It's a mess.
