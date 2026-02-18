import logging
import os
import json
from sqlalchemy import create_engine, text
from .base import CareStageStrategy
from model_registry import ModelRegistry

# Database configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "db", "health_companion.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"


class HomeTriageStrategy(CareStageStrategy):
    def get_metadata(self) -> dict:
        return {
            "title": "🏠 Home Self-Triage",
            "description": "AI Health Record Analysis (Logprobs Classification)",
            "inputs": [],
            "actions": [
                {"name": "analyze_trends", "label": "Analyse Health Records"}
            ]
        }

    def process_action(self, data: dict) -> dict:
        return self.analyze_trends()

    def analyze_trends(self):
        """Queries DB and uses AI logprobs to classify patient status across 5 dimensions."""
        try:
            data = self._fetch_patient_data()
            
            dimensions = [
                {
                    "name": "Metabolic Engine",
                    "focus": "Activity Volume",
                    "choices": ["Sedentary", "Maintenance", "Active", "Athletic"],
                    "prompt": self._build_metabolic_prompt(data)
                },
                {
                    "name": "Recovery Index",
                    "focus": "Sleep Health",
                    "choices": ["Deprived", "Fragmented", "Restored", "Excessive"],
                    "prompt": self._build_recovery_prompt(data)
                },
                {
                    "name": "Cardio Load",
                    "focus": "Heart Rate Zones",
                    "choices": ["Bradycardic", "Normal", "Elevated", "Strain"],
                    "prompt": self._build_cardio_prompt(data)
                },
                {
                    "name": "Circadian Rhythm",
                    "focus": "Routine Stability",
                    "choices": ["Chaotic", "Shifted", "Rhythmic", "Rigid"],
                    "prompt": self._build_circadian_prompt(data)
                },
                {
                    "name": "Medical Checkup Necessity",
                    "focus": "Risk Assessment",
                    "choices": ["Unnecessary", "Routine", "Recommended", "Urgent", "Critical"],
                    "prompt": self._build_checkup_prompt(data)
                }
            ]
            
            results = []
            for dim in dimensions:
                analysis = self._analyze_dimension(dim["name"], dim["choices"], dim["prompt"])
                analysis["focus"] = dim["focus"]
                results.append(analysis)

            return {
                "status": "success",
                "message": "Multi-dimensional Health Analysis Complete",
                "data": results,
                "metrics": data
            }

        except Exception as e:
            logging.error(f"Trend analysis failed: {e}")
            return {
                "status": "error",
                "message": f"Failed to analyze trends: {str(e)}",
                "data": []
            }

    def _fetch_patient_data(self):
        engine = create_engine(DATABASE_URL)
        data = {}
        with engine.connect() as conn:
            # 1. Activity (Last 7 days)
            res_act = conn.execute(text("""
                SELECT AVG(total_steps), AVG(calories), AVG(sedentary_minutes), AVG(very_active_minutes)
                FROM daily_activity ORDER BY activity_date DESC LIMIT 7
            """)).fetchone()
            data["avg_steps"] = round(res_act[0] or 0, 0)
            data["avg_cals"] = round(res_act[1] or 0, 0)
            data["avg_sedentary"] = round(res_act[2] or 0, 0)
            data["avg_active_mins"] = round(res_act[3] or 0, 0)
            
            # 2. Sleep (Last 7 days)
            res_sleep = conn.execute(text("""
                SELECT AVG(total_minutes_asleep), AVG(total_time_in_bed)
                FROM sleep_log ORDER BY sleep_day DESC LIMIT 7
            """)).fetchone()
            data["avg_sleep_mins"] = round(res_sleep[0] or 0, 0)
            data["avg_bed_mins"] = round(res_sleep[1] or 0, 0)
            data["sleep_hours"] = round(data["avg_sleep_mins"] / 60, 1)
            
            # 3. Heart Rate (Recent)
            res_hr = conn.execute(text("SELECT MAX(value), AVG(value) FROM heart_rate")).fetchone()
            data["max_hr"] = res_hr[0] or 0
            data["avg_hr"] = round(res_hr[1] or 0, 0)
            
        return data

    def _analyze_dimension(self, name, choices, prompt):
        # Call AI for logprobs
        probs = ModelRegistry.compute_choice_probabilities("consult_reasoning", prompt, choices)
        
        # Determine best fit
        best_choice = max(probs, key=probs.get)
        confidence = probs[best_choice]
        
        # Determine Color/Severity
        # Default: Green (good), Yellow (warning), Red (bad)
        # We need a mapping logic specifically per dimension, or simple heuristic
        severity = "green"
        if name == "Medical Checkup Necessity":
            if best_choice in ["Urgent", "Critical"]: severity = "red"
            elif best_choice in ["Recommended"]: severity = "yellow"
        elif name == "Metabolic Engine":
            if best_choice == "Sedentary": severity = "yellow"
        elif name == "Recovery Index":
            if best_choice in ["Deprived", "Excessive"]: severity = "yellow"
        elif name == "Cardio Load":
            if best_choice in ["Strain", "Elevated"]: severity = "yellow"
            if best_choice == "Bradycardic": severity = "yellow"
        elif name == "Circadian Rhythm":
            if best_choice in ["Chaotic", "Shifted"]: severity = "yellow"

        return {
            "dimension": name,
            "status": best_choice,
            "confidence": confidence,
            "severity": severity,
            "all_probs": probs
        }

    def _build_metabolic_prompt(self, data):
        prompt = (
            f"Analyze user metabolic activity.\n"
            f"Data: {data['avg_steps']} steps/day, {data['avg_active_mins']} active mins, {data['avg_sedentary']} sedentary mins.\n"
            f"Classify strictly as one of: [Sedentary, Maintenance, Active, Athletic].\n"
            f"Classification:"
        )
        return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"

    def _build_recovery_prompt(self, data):
        prompt = (
            f"Analyze user sleep recovery.\n"
            f"Data: {data['sleep_hours']} hours asleep, {data['avg_bed_mins']} mins in bed.\n"
            f"Classify strictly as one of: [Deprived, Fragmented, Restored, Excessive].\n"
            f"Classification:"
        )
        return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"

    def _build_cardio_prompt(self, data):
        prompt = (
            f"Analyze user cardio load.\n"
            f"Data: Max HR {data['max_hr']}, Avg HR {data['avg_hr']}.\n"
            f"Classify strictly as one of: [Bradycardic, Normal, Elevated, Strain].\n"
            f"Classification:"
        )
        return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
    
    def _build_circadian_prompt(self, data):
        # Note: Approximation due to lack of timestamps
        prompt = (
            f"Analyze user circadian rhythm stability.\n"
            f"Data: Avg sleep {data['sleep_hours']}h. (Timestamps unavailable, assume average stability).\n"
            f"Classify strictly as one of: [Chaotic, Shifted, Rhythmic, Rigid].\n"
            f"Classification:"
        )
        return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"

    def _build_checkup_prompt(self, data):
        prompt = (
            f"Analyze medical checkup necessity based on aggregation of risks.\n"
            f"Data: {data['avg_steps']} steps, {data['sleep_hours']}h sleep, Max HR {data['max_hr']}.\n"
            f"Classify strictly as one of: [Unnecessary, Routine, Recommended, Urgent, Critical].\n"
            f"Classification:"
        )
        return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
