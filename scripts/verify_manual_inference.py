
import os
import torch
import soundfile as sf
import numpy as np
import traceback
from transformers import AutoProcessor, AutoModelForCTC

# Paths
base_dir = r"c:\Users\s.claes\OneDrive - Accenture\AI_projects\Full-Lifecycle_Health_Companion"
model_path = os.path.join(base_dir, "ml_models", "medasr")
audio_path = os.path.join(base_dir, "data", "uploads", "Medical_conversations", "Data", "Audio Recordings", "CAR0001.mp3")

print(f"Model path: {model_path}")
print(f"Audio path: {audio_path}")

try:
    print("Loading processor and model...")
    processor = AutoProcessor.from_pretrained(model_path)
    model = AutoModelForCTC.from_pretrained(model_path)
    print("✅ Model loaded.")

    print("Loading audio...")
    # Use simple loading, assuming mono/16k for test or using pydub if soundfile fails
    try:
        data, sr = sf.read(audio_path)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        print(f"Audio loaded via soundfile. Shape: {data.shape}")
    except Exception as e:
        print(f"Soundfile failed: {e}. Trying pydub...")
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        data = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0 # Approx
        print(f"Audio loaded via pydub. Shape: {data.shape}")

    print("Running processor...")
    # Call processor. This triggers feature extraction.
    try:
        inputs = processor(data, sampling_rate=16000, return_tensors="pt")
        print("✅ Processor success. Inputs keys:", inputs.keys())
    except TypeError as e:
        print("❌ Processor TypeError!")
        traceback.print_exc()
        # Debugging what arg caused it?
        # Try without some args if possible, but processor usually has fixed signature.
        raise e

    print("Running model...")
    with torch.no_grad():
        logits = model(**inputs).logits
    
    print("Decoding...")
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]
    print("\nTranscription Result:")
    print(transcription[:200] + "...")

except Exception as e:
    print(f"❌ Script failed: {e}")
    traceback.print_exc()
