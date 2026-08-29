import re

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'r') as f:
    content = f.read()

# Replace V4RunResult instantiation at end of analyzePoints
# Find this block:
'''
                referencePoints = ptsToMeasureRef,
                observedPoints = transformedLens,
'''
# Replace with:
'''
                referencePoints = ptsToMeasureRef,
                observedPoints = filteredTransformedLens,
                localOutlierRejections = localOutlierIndices.size,
                crossingVectorRejections = crossingIndices.size,
                medianLocalResidual = medianLocalRes,
                madLocalResidual = madLocalRes,
                opticalRejectedReferencePoints = optRejectedRefPts,
                opticalRejectedObservedPoints = optRejectedLensPts,
'''

content = re.sub(
    r'referencePoints = ptsToMeasureRef,\s*observedPoints = transformedLens,',
    r'''referencePoints = ptsToMeasureRef,
                observedPoints = filteredTransformedLens,
                localOutlierRejections = localOutlierIndices.size,
                crossingVectorRejections = crossingIndices.size,
                medianLocalResidual = medianLocalRes,
                madLocalResidual = madLocalRes,
                opticalRejectedReferencePoints = optRejectedRefPts,
                opticalRejectedObservedPoints = optRejectedLensPts,''',
    content
)

with open('app/src/main/java/com/example/analysis/V4OpticalAnalyzer.kt', 'w') as f:
    f.write(content)
