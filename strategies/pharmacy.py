from .base import CareStageStrategy

class PharmacyStrategy(CareStageStrategy):
    def get_metadata(self) -> dict:
        return {
            "title": "💊 Precision Pharmacy",
            "description": "Prescription & Safety Checks",
            "content": [
                {"type": "text", "text": "Prescription: Lisinopril 10mg", "style": "highlight"},
                {"type": "text", "text": "Scanning for interactions...", "style": "info"}
            ],
            "actions": [
                {"name": "safety_check", "label": "Verify TxGemma Safety"}
            ]
        }

    def process_action(self, data: dict) -> dict:
        return {
            "status": "warning",
            "message": "Interaction Alert",
            "data": "Potential Lifestyle-Drug Interaction detected with high sodium intake.",
            "alert": True
        }
