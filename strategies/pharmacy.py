from .base import CareStageStrategy
import pandas as pd
import random
import re
import json
import os

from model_registry import ModelRegistry
from data.medical_vault import vault
from utils.logger import logger

# ═══════════════════════════════════════════════════════════════════════
# Static lookup: TDC task → concise GP-facing label
# These map the (A)/(B) predictions to ONE-LINE warnings.
# ═══════════════════════════════════════════════════════════════════════
TASK_GP_MAP = {
    "BBB_Martins": {
        "label": "Brain Penetration",
        "A": "Does not cross BBB",
        "B": "Crosses BBB — warn: drowsiness, dizziness",
        "risk_B": "yellow"
    },
    "Skin_Reaction": {
        "label": "Skin Reaction",
        "A": "Low skin reaction risk",
        "B": "Skin sensitization risk — watch for rash",
        "risk_B": "yellow"
    },
    "DILI": {
        "label": "Liver Toxicity",
        "A": "Low liver injury risk",
        "B": "DILI risk — limit alcohol, monitor LFTs",
        "risk_B": "red"
    },
    "hERG": {
        "label": "Heart Rhythm",
        "A": "Low cardiac risk",
        "B": "hERG blocker — warn: palpitations",
        "risk_B": "red"
    },
    "CYP3A4_Veith": {
        "label": "CYP3A4 Interaction",
        "A": "No CYP3A4 inhibition",
        "B": "Inhibits CYP3A4 — check interactions",
        "risk_B": "yellow"
    },
    "CYP2D6_Veith": {
        "label": "CYP2D6 Interaction",
        "A": "No CYP2D6 inhibition",
        "B": "Inhibits CYP2D6 — check interactions",
        "risk_B": "yellow"
    },
    "Bioavailability_Ma": {
        "label": "Oral Bioavailability",
        "A": "Low bioavailability (<20%)",
        "B": "Adequate bioavailability (≥20%)",
        "risk_A": "yellow"
    },
    "Half_Life_Obach": {
        "label": "Half-Life",
        # Regression task — handled separately
    },
}


def _parse_binary(raw: str) -> str | None:
    """
    Extract (A) or (B) from potentially noisy TxGemma-predict output.
    Returns 'A', 'B', or None if unparseable.
    """
    raw = raw.strip()
    # Clean: "(A)" or "(B)"
    m = re.search(r'\(([AB])\)', raw)
    if m:
        return m.group(1)
    # Noisy: starts with optional digit then A or B  (e.g. "1A", "2B")
    m = re.match(r'^\d*\s*([AB])\b', raw)
    if m:
        return m.group(1)
    # Single char
    if raw in ('A', 'B'):
        return raw
    return None


def _parse_halflife(raw: str) -> dict:
    """Parse regression half-life value → structured dict."""
    m = re.search(r'(\d+\.?\d*)', raw.strip())
    val_str = "Unknown"
    status = "yellow"
    
    if m:
        val = float(m.group(1))
        if val < 3:
            val_str = f"~{val}h (short)"
            status = "yellow" 
        elif val <= 12:
            val_str = f"~{val}h (medium)"
            status = "green"
        else:
            val_str = f"~{val}h (long)"
            status = "green"
    else:
        val_str = "Could not determine"
    
    return {"value": val_str, "status": status}


def _interpret_task(task: str, raw: str) -> dict:
    """Map a single TDC task raw output → structured result."""
    if task == "Half_Life_Obach":
        hl = _parse_halflife(raw)
        return {"value": hl["value"], "status": hl["status"]}

    label = _parse_binary(raw)
    mapping = TASK_GP_MAP.get(task)
    
    if not mapping:
        return {"value": raw, "status": "yellow"}
        
    if label and label in mapping:
        # Check if this outcome is risky
        risk_color = "green"
        if label == "A" and "risk_A" in mapping:
            risk_color = mapping["risk_A"]
        elif label == "B" and "risk_B" in mapping:
            risk_color = mapping["risk_B"]
            
        return {"value": mapping[label], "status": risk_color}
        
    return {"value": f"Unclear ({raw})", "status": "yellow"}


class PharmacyStrategy(CareStageStrategy):
    TDC_TASKS = [
        "BBB_Martins",
        "Skin_Reaction",
        "DILI",
        "hERG",
        "CYP3A4_Veith",
        "CYP2D6_Veith",
        "Bioavailability_Ma",
        "Half_Life_Obach",
    ]

    def __init__(self):
        super().__init__()
        self._tdc_prompts = None  # Lazy-loaded

    def _load_tdc_prompts(self) -> dict:
        """Load tdc_prompts.json once from the txgemma model directory."""
        if self._tdc_prompts is not None:
            return self._tdc_prompts

        model_path = ModelRegistry.get_model_path("txgemma_predict")
        json_path = os.path.join(model_path, "tdc_prompts.json")
        try:
            with open(json_path, "r") as f:
                self._tdc_prompts = json.load(f)
        except Exception as e:
            print(f"[Pharmacy] Failed to load tdc_prompts.json: {e}")
            self._tdc_prompts = {}
        return self._tdc_prompts

    def _load_random_medicines(self, n=2):
        """Loads FDA structures and selects n random medicines."""
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "uploads",
            "FDA_Approved_structures.csv"
        )
        try:
            df = pd.read_csv(csv_path)
            if "Name" not in df.columns or "SMILES" not in df.columns:
                print("CSV missing Name or SMILES columns.")
                return []
            df = df.dropna(subset=["Name", "SMILES"])
            if len(df) < n:
                return df.to_dict("records")
            return df.sample(n).to_dict("records")
        except Exception as e:
            print(f"Error loading medicines: {e}")
            return []

    def _predict_properties(self, smiles: str) -> dict:
        """
        Run TxGemma-predict for all TDC tasks on a SMILES string.
        """
        tdc_prompts = self._load_tdc_prompts()
        results = {}

        for task in self.TDC_TASKS:
            template = tdc_prompts.get(task)
            if not template:
                results[task] = "TASK_NOT_FOUND"
                continue

            # ── Build prompt exactly per TxGemma model card ──
            prompt = template.replace("{Drug SMILES}", smiles)

            # ── Run inference with SHORT generation ──
            is_regression = (task == "Half_Life_Obach")
            max_tokens = 8 if is_regression else 4

            raw = ModelRegistry.run_inference(
                "txgemma_predict", prompt, max_new_tokens=max_tokens
            )
            results[task] = raw.strip()

        return results

    def _build_drug_data(self, name: str, smiles: str, preds: dict) -> dict:
        """
        Build a structured dictionary for one drug.
        """
        checks = []
        for task in self.TDC_TASKS:
            raw = preds.get(task, "N/A")
            gp_label = TASK_GP_MAP.get(task, {}).get("label", task)
            interpreted = _interpret_task(task, raw)
            
            checks.append({
                "label": gp_label,
                "value": interpreted["value"],
                "status": interpreted["status"]
            })

        return {
            "name": name,
            "smiles": smiles,
            "checks": checks
        }

    def get_metadata(self) -> dict:
        return {
            "title": "💊 Precision Pharmacy",
            "description": "TxGemma Drug Analysis",
            "content": [
                {"type": "text", "text": "AI-Powered Safety Checks Ready", "style": "highlight"},
                {"type": "text", "text": "Click 'Analyze Random Drugs' to demo.", "style": "info"},
            ],
            "actions": [
                {"name": "analyze_drugs", "label": "Analyze 2 Random Drugs"}
            ],
        }

    def process_action(self, data: dict) -> dict:
        action = data.get("action")

        if action == "save_analysis":
            return self.save_analysis(data.get("payload"))

        if action == "analyze_drugs":
            medicines = self._load_random_medicines(2)
            if not medicines:
                return {
                    "status": "error",
                    "message": "Data Load Failed",
                    "data": "Could not load FDA_Approved_structures.csv.",
                }

            drugs_data = []
            summary_inputs = []

            for med in medicines:
                preds = self._predict_properties(med["SMILES"])
                drug_info = self._build_drug_data(med["Name"], med["SMILES"], preds)
                drugs_data.append(drug_info)
                
                # Collect warnings for summary
                warnings = [c["value"] for c in drug_info["checks"] if c["status"] in ["red", "yellow"]]
                if warnings:
                    summary_inputs.append(f"{med['Name']}: {'; '.join(warnings)}")
                else:
                    summary_inputs.append(f"{med['Name']}: No major warnings.")

            # ── TxGemma Summary ──
            # Using TxGemma instead of MedGemma as requested.
            summary_prompt = (
                "Summarize these drug safety warnings for a patient. Keep it simple.\n"
                f"{' '.join(summary_inputs)}\n"
                "Summary:"
            )
            
            # TxGemma is small, keep prompt simple
            patient_summary = ModelRegistry.run_inference(
                "txgemma_predict", summary_prompt, max_new_tokens=64
            )

            return {
                "status": "success",
                "message": "Analysis Complete",
                "data": {
                    "drugs": drugs_data,
                    "summary": patient_summary
                },
                "alert": True,
            }

        return {
            "status": "warning",
            "message": "Unknown Action",
            "data": "Action not recognized.",
            "alert": False,
        }

    def save_analysis(self, payload):
        """Manually saves analysis results to the vault."""
        try:
            if not payload:
                return {"status": "error", "message": "No data to save"}
            
            logger.info("Pharmacy Manual Save Requested.")
            # Store in Medical Vault
            entry_id = vault.store_entry(
                category="Pharmacy Analysis",
                content=payload,
                tags=["Pharmacy", "AI", "TxGemma"]
            )
            return {
                "status": "success", 
                "message": "Analysis saved to Vault successfully!", 
                "data": {"id": entry_id}
            }
        except Exception as e:
            logger.error(f"Pharmacy Save failed: {e}")
            return {"status": "error", "message": f"Save failed: {str(e)}"}
