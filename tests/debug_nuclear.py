import sys
import os
import torch
import torchaudio
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_registry import ModelRegistry

# Path to the audio file
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
audio_path = os.path.join(base_dir, "data", "uploads", "Medical_conversations", "Data", "Audio Recordings", "CAR0001.mp3")

print(f"Debugging Nuclear Option for: {audio_path}")

try:
    # Load model
    path = ModelRegistry.get_model_path("medasr")
    from transformers import AutoProcessor, AutoModelForCTC
    processor = AutoProcessor.from_pretrained(path)
    model = AutoModelForCTC.from_pretrained(path)
    
    # Manual Feature Extraction (Nuclear Option Logic)
    waveform, sr = torchaudio.load(audio_path, num_frames=16000*30) # Only load 30s
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        waveform = resampler(waveform)
    
    if len(waveform.shape) == 1:
        waveform = waveform.unsqueeze(0)
    waveform = waveform.to(torch.float32)
    
    # Standard Kaldi Fbank
    features = torchaudio.compliance.kaldi.fbank(
        waveform, 
        num_mel_bins=128,
        sample_frequency=16000,
        frame_length=25.0, 
        frame_shift=10.0,
        subtract_mean=True
    )
    
    # Normalize (Standard Wav2Vec2/Hubert expectation: zero mean, unit variance)
    features = features - features.mean()
    features = features / (features.std() + 1e-6)

    input_features = features.unsqueeze(0)
    
    print(f"Features: shape={input_features.shape}, min={input_features.min()}, max={input_features.max()}, mean={input_features.mean()}")
    
    with torch.no_grad():
        logits = model(input_features).logits
    
    print(f"Logits: shape={logits.shape}")
    
    # Check predictions
    predicted_ids = torch.argmax(logits, dim=-1)
    print(f"Predicted IDs (first 50): {predicted_ids[0, :50].tolist()}")
    
    unique, counts = torch.unique(predicted_ids, return_counts=True)
    print(f"Unique tokens predicted: {dict(zip(unique.tolist(), counts.tolist()))}")
    
    # decode
    text = processor.decode(predicted_ids[0], skip_special_tokens=True)
    print(f"Decoded Text: '{text}'")
    
except Exception as e:
    print(f"Error: {e}")
