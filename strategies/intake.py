from .base import CareStageStrategy
from model_registry import ModelRegistry
import json

class IntakeStrategy(CareStageStrategy):
    def get_metadata(self) -> dict:
        return {
            "title": "📋 Pre-Consult Intake",
            "description": "Patient Intake & AI Interview",
            "content": [], # Content managed dynamically by chat
            "actions": [
                {"name": "start_intake", "label": "Start Interview", "hidden": True},
                {"name": "send_message", "label": "Send", "hidden": True},
                {"name": "generate_report", "label": "Finish & Report", "hidden": True},
                {"name": "save_pre_briefing", "label": "Save to Vault", "hidden": True}
            ],
            "inputs": [] # Inputs handled by custom chat UI
        }

    def process_action(self, data: dict) -> dict:
        action = data.get("action")
        payload = data.get("payload", {})
        
        if action == "start_intake":
            return self.start_intake()
        elif action == "send_message":
            return self.process_message(payload)
        elif action == "generate_report":
            return self.generate_report(payload)
        elif action == "save_pre_briefing":
            return self.save_pre_briefing(payload)
        else:
            return {"status": "error", "message": "Unknown action"}

    def start_intake(self):
        initial_message = "Hello. I am your pre-consult assistant. To help the doctor prepare, could you please tell me the main reason for your visit today?"
        return {
            "status": "success",
            "data": {
                "message": initial_message,
                "history": [{"role": "assistant", "content": initial_message}],
                "turn_count": 0
            }
        }

    def process_message(self, payload: dict):
        history = payload.get("history", [])
        user_msg = payload.get("message")
        turn_count = payload.get("turn_count", 0)

        # Append user message
        history.append({"role": "user", "content": user_msg})

        # Generate AI response
        # Construct prompt from history
        conversation_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
        
        system_prompt = (
            "You are an empathetic medical assistant conducting a pre-consult intake interview. "
            "Your goal is to gather relevant clinical information for the doctor. "
            "Ask ONE clear follow-up question based on the patient's last response. "
            "Do not diagnose. Keep your response brief and professional."
        )

        prompt = f"{system_prompt}\n\nConversation so far:\n{conversation_text}\n\nASSISTANT:"

        # Call MedGemma (or Intake model if specialized)
        # Using 'intake_chat' role which maps to TxGemma-2b (fast) or MedGemma if unavailable logic in registry
        # Actually ModelRegistry logic has a fallback.
        
        ai_response = ModelRegistry.run_inference("intake_chat", prompt)
        
        # Clean up response (sometimes models generate too much or echo)
        ai_response = ai_response.replace("ASSISTANT:", "").strip()
        if "USER:" in ai_response:
            ai_response = ai_response.split("USER:")[0].strip()

        history.append({"role": "assistant", "content": ai_response})

        return {
            "status": "success",
            "data": {
                "message": ai_response,
                "history": history,
                "turn_count": turn_count + 1
            }
        }

    def generate_report(self, payload: dict):
        history = payload.get("history", [])
        
        conversation_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])
        
        system_prompt = (
            "Summarize the following patient intake interview into a structured Pre-Briefing Note for a physician. "
            "Include: \n1. Chief Complaint\n2. History of Present Illness\n3. Relevant Context\n"
            "Format clearly. Do not invent information not present in the interview."
        )

        prompt = f"{system_prompt}\n\nInterview Transcript:\n{conversation_text}\n\nPRE-BRIEFING NOTE:"

        # Use a stronger model for summarization if available, e.g., 'consult_reasoning' (MedGemma 4B)
        report = ModelRegistry.run_inference("consult_reasoning", prompt)
        
        # Cleanup
        report = report.replace("PRE-BRIEFING NOTE:", "").strip()

        return {
            "status": "success",
            "message": "Pre-Briefing Note Generated",
            "data": {
                "report": report,
                "history": history
            }
        }

    def save_pre_briefing(self, payload: dict):
        from data.medical_vault import vault
        
        report = payload.get("report")
        
        if not report:
             return {"status": "error", "message": "No report to save"}

        entry_id = vault.store_entry(
            category="clinical_note",
            content=report,
            tags=["pre_briefing", "intake", "soap", "Pre-Consult Intake AI"]
        )
        
        return {
            "status": "success",
            "message": f"Saved to Medical Vault",
            "data": {"id": entry_id}
        }
