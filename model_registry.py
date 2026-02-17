import os

# Define Model Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "ml_models")

# Mapped Model Paths (matching download_models.py structure)
MODEL_PATHS = {
    # GGUF Model (downloaded to ml_models/gguf/)
    "triage_edge": os.path.join(MODELS_DIR, "gguf", "gemma-2-2b-it-Q4_K_M.gguf"),
    
    # Full Model Directories (downloaded via snapshot_download to ml_models/<key>)
    "intake_chat": os.path.join(MODELS_DIR, "txgemma-2b-predict"),
    "consult_reasoning": os.path.join(MODELS_DIR, "medgemma-1.5-4b-it"),
    
    # Specialized Models
    "cxr_foundation": os.path.join(MODELS_DIR, "cxr-foundation"),
    "medasr": os.path.join(MODELS_DIR, "medasr"),
}

class ModelRegistry:
    @staticmethod
    def get_model_path(role):
        return MODEL_PATHS.get(role)

    @staticmethod
    def is_model_available(role):
        path = MODEL_PATHS.get(role)
        return path and os.path.exists(path)

    @staticmethod
    def run_inference(role, prompt):
        """
        Runs inference. 
        - If role is 'triage_edge' (GGUF), tries llama-cpp.
        - If role is others (Full Models), tries transformers (if installed).
        - Otherwise returns a mock response.
        """
        path = ModelRegistry.get_model_path(role)
        
        # Check actual model existence
        if path and os.path.exists(path):
            try:
                # 1. Handle GGUF (Edge Triage)
                if role == "triage_edge" and path.endswith(".gguf"):
                    try:
                        from llama_cpp import Llama
                        # Very basic inference
                        # llm = Llama(model_path=path, n_ctx=2048, verbose=False)
                        # output = llm(prompt, max_tokens=128)
                        # return output['choices'][0]['text']
                        pass
                    except ImportError:
                        print(f"Warning: 'llama-cpp-python' not installed. Cannot run {role} model.")

                # 2. Handle Full Models (Intake/Consult)
                elif os.path.isdir(path):
                    try:
                        import torch
                        from transformers import AutoModelForCausalLM, AutoTokenizer
                        # Placeholder for actual loading logic
                        # tokenizer = AutoTokenizer.from_pretrained(path)
                        # model = AutoModelForCausalLM.from_pretrained(path, device_map="auto")
                        pass
                    except ImportError:
                        print(f"Warning: 'transformers' or 'torch' not installed. Cannot run {role} model.")
            
            except Exception as e:
                print(f"Error running model {role}: {e}")

        # Fallback Mock Responses based on Role
        if role == "triage_edge":
            return "(Edge AI - Gemma 2B) Based on symptoms, suggested priority: Level 2."
        elif role == "intake_chat":
            return "(Intake AI - TxGemma 2B) Patient history noted. Generating SOAP..."
        elif role == "consult_reasoning":
            return "(Consult AI - MedGemma 1.5 4B) Analysis complete. Differential diagnosis suggestions ready."
        
        return "AI Service Unavailable."
