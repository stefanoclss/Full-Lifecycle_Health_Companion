from .base import CareStageStrategy
from model_registry import ModelRegistry

class IntakeStrategy(CareStageStrategy):
    def get_metadata(self) -> dict:
        return {
            "title": "📋 Pre-Consult Intake",
            "description": "Patient Intake & History",
            "content": [
                {"type": "table", "headers": ["Intake Question", "Patient Response"], "rows": [
                    ["Occupation", "Construction - High Activity"],
                    ["Smoker", "No"]
                ]}
            ],
            "actions": [
                {"name": "generate_soap", "label": "Generate SOAP Note"}
            ]
        }

    def process_action(self, data: dict) -> dict:
        # Use ModelRegistry
        note = ModelRegistry.run_inference("intake_chat", "Generate SOAP note based on intake data.")
        
        return {
            "status": "success",
            "message": "SOAP Note Generated",
            "data": note,
            "alert": True
        }
