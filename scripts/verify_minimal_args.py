
import os
import numpy as np
import traceback
from transformers import AutoProcessor

base_dir = r"c:\Users\s.claes\OneDrive - Accenture\AI_projects\Full-Lifecycle_Health_Companion"
model_path = os.path.join(base_dir, "ml_models", "medasr")

print(f"Loading processor from {model_path}...")
try:
    processor = AutoProcessor.from_pretrained(model_path)
    fe = processor.feature_extractor
    
    # Create dummy audio
    dummy_audio = np.random.uniform(-1, 1, 16000).astype(np.float32)
    
    print("\n--- Test A: audio + sr (NO return_tensors) ---")
    try:
        out = fe(dummy_audio, sampling_rate=16000)
        print("✅ Success A!")
        if hasattr(out, "input_features"):
            print("Shape:", np.array(out.input_features).shape)
        elif isinstance(out, dict):
             print("Keys:", out.keys())
             for k,v in out.items():
                 print(f"{k} shape: {np.array(v).shape}")
    except Exception as e:
        print(f"❌ Fail A: {e}")
        traceback.print_exc()

except Exception as e:
    traceback.print_exc()
