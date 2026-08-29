#!/bin/bash
for file in app/src/main/java/com/example/ui/ExperimentScreen.kt app/src/main/java/com/example/ui/FocusExperimentScreen.kt app/src/main/java/com/example/ui/LensExperimentScreen.kt; do
    sed -i 's/cameraProvider\.unbindAll()/previewRef?.let { cameraProvider.unbind(it) }; imageAnalysisRef?.let { cameraProvider.unbind(it) }/g' $file
    sed -i 's/provider\.unbindAll()/previewRef?.let { provider.unbind(it) }; imageAnalysisRef?.let { provider.unbind(it) }/g' $file
done
