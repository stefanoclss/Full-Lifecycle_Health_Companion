import logging
from .base import CareStageStrategy
from model_registry import ModelRegistry

class HomeTriageStrategy(CareStageStrategy):
    def get_metadata(self) -> dict:
        return {
            "title": "🏠 Home Self-Triage",
            "description": "MedASR Voice / Derm Photo Triage",
            "inputs": [
                {"name": "description", "label": "Describe symptoms or upload photo path", "type": "text", "placeholder": "Describe symptoms..."}
            ],
            "actions": [
                {"name": "analyze", "label": "Run Edge AI Analysis"}
            ]
        }

    def process_action(self, data: dict) -> dict:
        user_input = data.get("description", "")
        
        # Use ModelRegistry for AI inference
        result = ModelRegistry.run_inference("triage_edge", f"Analyze symptoms: {user_input}")
        
        return {
            "status": "success",
            "message": "Analysis Complete",
            "data": result,
            "alert": True
        }
