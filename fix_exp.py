with open('app/src/main/java/com/example/ui/ExperimentScreen.kt', 'r') as f:
    content = f.read()

bad_block = """                    } catch (exc: Exception) {
                        flashAvailable = false
                    }
                }, ContextCompat.getMainExecutor(context))
            } else if (event == androidx.lifecycle.Lifecycle.Event.ON_PAUSE) {
                if (cameraProviderFuture.isDone) {
                    val provider = cameraProviderFuture.get()
                    imageAnalysisRef?.clearAnalyzer()
                    provider.unbindAll()
                }
            }
        }
        
        lifecycle.addObserver(observer)
        
        onDispose {"""

good_block = """                    } catch (exc: Exception) {
                        flashAvailable = false
                    }
                }, ContextCompat.getMainExecutor(context))
        
        onDispose {"""

content = content.replace(bad_block, good_block)

with open('app/src/main/java/com/example/ui/ExperimentScreen.kt', 'w') as f:
    f.write(content)
