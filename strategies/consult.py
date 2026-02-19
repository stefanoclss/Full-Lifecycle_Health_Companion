from .base import CareStageStrategy
from model_registry import ModelRegistry

class ConsultStrategy(CareStageStrategy):
    def get_metadata(self) -> dict:
        return {
            "title": "🩺 Clinical Consultation",
            "description": "AI-Augmented Physician Tools",
        "inputs": [],
            "actions": [
                {"name": "get_audio", "label": "Load Audio", "hidden": True},
                {"name": "transcribe", "label": "Start Transcription", "hidden": True},
                {"name": "generate_note", "label": "Generate Clinical Note", "hidden": True},
                {"name": "save_note", "label": "Save to Vault", "hidden": True},
                {"name": "cxr", "label": "Analyze CXR (X-Ray)", "hidden": True},
                {"name": "pathology", "label": "Pathology View", "hidden": True},
                {"name": "diff_dx", "label": "Differential DX", "hidden": True}
            ]
        }

    def process_action(self, data: dict) -> dict:
        action = data.get("action", "unknown")
        payload = data.get("payload", {})
        
        if action == "get_audio":
            # Return path to the specific audio file
            # Assuming server mounts /data
            return {
                "status": "success",
                "data": {"url": "/data/uploads/Medical_conversations/Data/Audio Recordings/CAR0001.mp3"}
            }

        elif action == "transcribe":
            return self.transcribe_audio()

        elif action == "generate_note":
            return self.generate_clinical_note(payload.get("transcript"))

        elif action == "save_note":
            return self.save_clinical_note(payload.get("note"))

        elif action == "diff_dx":
             # Use the large reasoning model
             result = ModelRegistry.run_inference("consult_reasoning", "Generate differential diagnosis.")
             return {"status": "success", "data": result}
        
        else:
             # Mock responses for others
             responses = {
                "cxr": "Chest X-Ray Analyzed: Clear fields.",
                "pathology": "Pathology slides loaded."
            }
             result = responses.get(action, "Unknown action")
             return {"status": "success", "data": result}

    def transcribe_audio(self):
        import os
        # Locate the file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        audio_path = os.path.join(base_dir, "data", "uploads", "Medical_conversations", "Data", "Audio Recordings", "CAR0001.mp3")
        
        if not os.path.exists(audio_path):
            return {"status": "error", "message": f"Audio file not found at {audio_path}"}
        
        # Call Registry
        result = ModelRegistry.transcribe_audio("medasr", audio_path)
        
        if "text" in result and result["text"].startswith("Error"):
             return {"status": "error", "message": result["text"]}
             
        return {
            "status": "success",
            "message": "Transcription Complete",
            "data": result # Contains text and segments
        }

    def generate_clinical_note(self, transcript):
        if not transcript:
            return {"status": "error", "message": "No transcript provided"}
            
        # Highly optimized, low-token system prompt.
        # Directives like "medical shorthand" and "strictly concise" drastically reduce output tokens.
        system_prompt = (
            "Role: PA. Synthesize transcript into:\n"
            "1. Key Points\n"
            "2. SOAP Note\n"
            "Constraint: Be strictly concise. Use standard medical shorthand. Synthesize, do not repeat."
        )
        
        prompt = f"{system_prompt}\nTranscript:\n{transcript}\nNOTE:"
        
        note = ModelRegistry.run_inference("consult_reasoning", prompt)
        
        # Cleanup
        note = note.replace("NOTE:", "").strip()


        return {
            "status": "success",
            "data": {"note": note}
        }

    def save_clinical_note(self, note):
        from data.medical_vault import vault
        
        if not note:
            return {"status": "error", "message": "No note to save"}

        entry_id = vault.store_entry(
            category="clinical_note",
            content=note,
            tags=["consultation", "audio_summary", "CAR0001"],
        )
        
        return {
            "status": "success",
            "message": "Clinical Note Saved to Vault",
            "data": {"id": entry_id}
        }
