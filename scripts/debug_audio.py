
import sys
import os
import traceback

print("--- Python Info ---")
print(sys.executable)
print(sys.version)

print("\n--- Testing Imports ---")
try:
    import soundfile
    print(f"✅ soundfile imported. Version: {soundfile.__version__}")
except ImportError as e:
    print(f"❌ soundfile import failed: {e}")
except Exception as e:
    print(f"❌ soundfile import error: {e}")

try:
    import librosa
    print(f"✅ librosa imported. Version: {librosa.__version__}")
except ImportError as e:
    print(f"❌ librosa import failed: {e}")

try:
    import torch
    print(f"✅ torch imported. Version: {torch.__version__}")
except ImportError as e:
    print(f"❌ torch import failed: {e}")

try:
    import transformers
    print(f"✅ transformers imported. Version: {transformers.__version__}")
except ImportError as e:
    print(f"❌ transformers import failed: {e}")

print("\n--- Testing Audio Load (pydub) ---")
audio_path = r"c:\Users\s.claes\OneDrive - Accenture\AI_projects\Full-Lifecycle_Health_Companion\data\uploads\Medical_conversations\Data\Audio Recordings\CAR0001.mp3"
if os.path.exists(audio_path):
    print(f"Audio file found: {audio_path}")
    try:
        from pydub import AudioSegment
        import numpy as np
        audio = AudioSegment.from_file(audio_path)
        print(f"✅ Pydub loaded audio. Duration: {len(audio)}ms")
        
        # Convert to numpy float32 16kHz mono
        audio = audio.set_frame_rate(16000).set_channels(1)
        samples = np.array(audio.get_array_of_samples())
        # Normalize to -1.0 to 1.0
        if audio.sample_width == 2:
            data = samples.astype(np.float32) / 32768.0
        elif audio.sample_width == 4:
            data = samples.astype(np.float32) / 2147483648.0
        else:
            data = samples.astype(np.float32)
            
        print(f"✅ Converted to numpy: {data.shape} @ 16kHz")
    except Exception as e:
        print(f"❌ Pydub load failed: {e}")
        data = None
else:
    print(f"❌ Audio file NOT found at {audio_path}")

print("\n--- Testing Pipeline ---")
try:
    from transformers import pipeline
    # Use the path from the registry logic
    base_dir = r"c:\Users\s.claes\OneDrive - Accenture\AI_projects\Full-Lifecycle_Health_Companion"
    model_path = os.path.join(base_dir, "ml_models", "medasr")
    
    if os.path.exists(model_path):
        print(f"Loading model from {model_path}...")
        transcriber = pipeline(
            "automatic-speech-recognition", 
            model=model_path, 
            chunk_length_s=30
        )
        print("✅ Pipeline loaded.")
        
        if data is not None:
            print("Running inference on numpy data with return_timestamps='word'...")
            try:
                res = transcriber({"raw": data, "sampling_rate": 16000}, return_timestamps="word")
                print("✅ Inference SUCCESS (numpy)!")
                print(str(res)[:100])
            except Exception as e:
                print(f"❌ Inference FAILED (numpy): {e}")
                traceback.print_exc()
        
        print("Running inference on filepath with return_timestamps='word'...")
        try:
            res = transcriber(audio_path, return_timestamps="word")
            print("✅ Inference SUCCESS (file)!")
        except Exception as e:
            print(f"❌ Inference FAILED (file): {e}")

    else:
        print(f"❌ Model path not found: {model_path}")

except Exception as e:
    print(f"❌ Pipeline setup failed: {e}")
    traceback.print_exc()
