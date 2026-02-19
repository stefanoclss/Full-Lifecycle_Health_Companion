
import os
import torch
import torchaudio
import numpy as np
import traceback
from transformers import AutoModelForCTC

# Settings
num_mel_bins = 128
target_sr = 16000

base_dir = r"c:\Users\s.claes\OneDrive - Accenture\AI_projects\Full-Lifecycle_Health_Companion"
model_path = os.path.join(base_dir, "ml_models", "medasr")

print(f"Loading model from {model_path}...")
try:
    model = AutoModelForCTC.from_pretrained(model_path)
    print("✅ Model loaded.")
    
    # Create dummy audio (1 sec)
    waveform = torch.randn(1, 16000) # (channel, time)
    
    print("\n--- Test: Torchaudio Fbank ---")
    try:
        # Standard Kaldi fbank parameters often used
        # We assume 16k sr, 128 bins.
        features = torchaudio.compliance.kaldi.fbank(
            waveform, 
            num_mel_bins=num_mel_bins,
            sample_frequency=target_sr,
            frame_length=25.0, 
            frame_shift=10.0,
            subtract_mean=True # Often helpful
        )
        print(f"Features shape: {features.shape}")
        
        # Add batch dim: (time, freq) -> (1, time, freq)
        input_features = features.unsqueeze(0)
        
        print("Running model forward pass...")
        with torch.no_grad():
            out = model(input_features)
        
        print(f"✅ Success! Logits shape: {out.logits.shape}")

    except Exception as e:
        print(f"❌ Fail: {e}")
        traceback.print_exc()

except Exception as e:
    traceback.print_exc()
