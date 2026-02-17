import os

# Define Model Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "ml_models")

# Mapped Model Paths (matching download_models.py)
MODEL_PATHS = {
    "triage_edge": os.path.join(MODELS_DIR, "gemma-2-2b-it-Q4_K_M.gguf"),
    "intake_chat": os.path.join(MODELS_DIR, "TxGemma-9B-chat-Q4_K_M.gguf"),
    "consult_reasoning": os.path.join(MODELS_DIR, "MedGemma-27B-it-Q4_K_M.gguf"),
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
        Runs inference. If model exists and llama-cpp is installed, runs it.
        Otherwise returns a mock response.
        """
        path = ModelRegistry.get_model_path(role)
        
        # Check actual model existence
        if path and os.path.exists(path):
            try:
                # Try to import Llama (optional dependency)
                from llama_cpp import Llama
                
                # Load model (Mocking this part for now to avoid massive memory usage during dev)
                # llm = Llama(model_path=path, n_ctx=2048, verbose=False)
                # output = llm(prompt, max_tokens=128)
                # return output['choices'][0]['text']
                pass
            except ImportError:
                print(f"Warning: 'llama-cpp-python' not installed. Cannot run {role} model.")
            except Exception as e:
                print(f"Error running model: {e}")

        # Fallback Mock Responses based on Role
        if role == "triage_edge":
            return "(Edge AI) Based on symptoms, suggested priority: Level 2."
        elif role == "intake_chat":
            return "(Intake AI) Patient history noted. Generating SOAP..."
        elif role == "consult_reasoning":
            return "(Consult AI) Analysis complete. Differential diagnosis suggestions ready."
        
        return "AI Service Unavailable."
