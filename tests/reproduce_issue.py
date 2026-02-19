import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_registry import ModelRegistry

# Path to the audio file
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
audio_path = os.path.join(base_dir, "data", "uploads", "Medical_conversations", "Data", "Audio Recordings", "CAR0001.mp3")

print(f"Testing transcription for: {audio_path}")

try:
    # Force the manual inference path by mocking pipeline failure or just rely on current behavior if it's already failing
    # For now, let's run it as is. If the user says it's broken, it's likely hitting the fallback naturally.
    result = ModelRegistry.transcribe_audio("medasr", audio_path)
    print("Transcription Result:")
    print(result.get("text", "No text found"))
except Exception as e:
    print(f"Error: {e}")
