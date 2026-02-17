from .base import CareStageStrategy
from model_registry import ModelRegistry

class ConsultStrategy(CareStageStrategy):
    def get_metadata(self) -> dict:
        return {
            "title": "🩺 Clinical Consultation",
            "description": "AI-Augmented Physician Tools",
            "actions": [
                {"name": "cxr", "label": "Analyze CXR (X-Ray)"},
                {"name": "transcribe", "label": "Live Transcription"},
                {"name": "pathology", "label": "Pathology View"},
                {"name": "diff_dx", "label": "Differential DX"}
            ]
        }

    def process_action(self, data: dict) -> dict:
        action = data.get("action", "unknown")
        
        result = "Action executed."
        if action == "diff_dx":
             # Use the large reasoning model
             result = ModelRegistry.run_inference("consult_reasoning", "Generate differential diagnosis.")
        else:
             # Mock responses for others for now
             responses = {
                "cxr": "Chest X-Ray Analyzed: Clear fields.",
                "transcribe": "Transcription started...",
                "pathology": "Pathology slides loaded."
            }
             result = responses.get(action, "Unknown action")

        return {
            "status": "success",
            "message": f"Action '{action}' executed.",
            "data": result
        }
