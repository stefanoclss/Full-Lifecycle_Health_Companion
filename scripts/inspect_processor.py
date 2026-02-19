
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
    print(f"Feature Extractor: {fe}")
    print(f"FE Class: {type(fe)}")
    
    # Create dummy audio
    dummy_audio = np.random.uniform(-1, 1, 16000).astype(np.float32)
    
    # Test 1: Direct call with minimal args
    print("\n--- Test 1: Minimal Args ---")
    try:
        out = fe(dummy_audio, sampling_rate=16000)
        print("✅ Success! Keys:", out.keys())
    except Exception as e:
        print(f"❌ Fail: {e}")
        
    # Test 2: Standard call (likely what processor does)
    print("\n--- Test 2: With return_tensors='pt' ---")
    try:
        out = fe(dummy_audio, sampling_rate=16000, return_tensors="pt")
        print("✅ Success! Keys:", out.keys())
    except Exception as e:
        print(f"❌ Fail: {e}")

    # Test 3: With padding (processor might add this)
    print("\n--- Test 3: With padding ---")
    try:
        out = fe(dummy_audio, sampling_rate=16000, padding=True)
        print("✅ Success! Keys:", out.keys())
    except Exception as e:
        print(f"❌ Fail: {e}")
        
    # Check inspect signature
    import inspect
    if hasattr(fe, "_torch_extract_fbank_features"):
        sig = inspect.signature(fe._torch_extract_fbank_features)
        print(f"\nSignature of _torch_extract_fbank_features: {sig}")
    
    if hasattr(fe, "__call__"):
         sig = inspect.signature(fe.__call__)
         print(f"Signature of __call__: {sig}")

except Exception as e:
    traceback.print_exc()
