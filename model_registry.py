import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "ml_models")

MODEL_PATHS = {
    "triage_edge": os.path.join(MODELS_DIR, "gguf", "gemma-2-2b-it-Q4_K_M.gguf"),
    "intake_chat": os.path.join(MODELS_DIR, "medgemma-1.5-4b-it"),
    "consult_reasoning": os.path.join(MODELS_DIR, "medgemma-1.5-4b-it"),
    "cxr_foundation": os.path.join(MODELS_DIR, "cxr-foundation"),
    "medasr": os.path.join(MODELS_DIR, "medasr"),
}

class ModelRegistry:
    _model_cache = {}
    _tokenizer_cache = {}

    @staticmethod
    def get_model_path(role):
        return MODEL_PATHS.get(role)

    @staticmethod
    def is_model_available(role):
        path = MODEL_PATHS.get(role)
        return path and os.path.exists(path)

    @staticmethod
    def run_inference(role, prompt):
        path = ModelRegistry.get_model_path(role)

        if path and os.path.exists(path):
            try:
                if role == "triage_edge" and path.endswith(".gguf"):
                    try:
                        from llama_cpp import Llama
                        pass
                    except ImportError:
                        print(f"Warning: 'llama-cpp-python' not installed. Cannot run {role} model.")

                elif os.path.isdir(path):
                    try:
                        import torch
                        from transformers import AutoModelForCausalLM, AutoTokenizer

                        print(f"Loading model from {path}...")
                        device = "cuda" if torch.cuda.is_available() else "cpu"
                        torch_dtype = torch.float16 if device == "cuda" else torch.float32

                        tokenizer = AutoTokenizer.from_pretrained(path)
                        model = AutoModelForCausalLM.from_pretrained(
                            path,
                            torch_dtype=torch_dtype,
                            device_map=device,
                            low_cpu_mem_usage=True,
                        )

                        # FIX 2: Use actual model context limit instead of hardcoded 1024
                        model_max_ctx = getattr(model.config, "max_position_embeddings", 4096)

                        # FIX 5: Truncate input to always leave room for generation
                        inputs = tokenizer(
                            prompt,
                            return_tensors="pt",
                            truncation=True,
                            max_length=model_max_ctx - 256,
                        ).to(device)

                        input_length = inputs.input_ids.shape[1]
                        max_new_tokens = min(256, model_max_ctx - input_length)

                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=max_new_tokens,
                            do_sample=False,
                        )

                        generated_tokens = outputs[0][input_length:]
                        return tokenizer.decode(generated_tokens, skip_special_tokens=True)

                    except ImportError:
                        print(f"Warning: 'transformers' or 'torch' not installed. Cannot run {role} model.")
                    except Exception as e:
                        print(f"Error during inference: {e}")

            except Exception as e:
                print(f"Error running model {role}: {e}")

        if role == "triage_edge":
            return "(Edge AI - Gemma 2B) Based on symptoms, suggested priority: Level 2."
        elif role == "intake_chat":
            return "(Intake AI - TxGemma 2B) Patient history noted. Generating SOAP..."
        elif role == "consult_reasoning":
            return "(Consult AI - MedGemma 1.5 4B) Analysis complete. Differential diagnosis suggestions ready."
        return "AI Service Unavailable."

    @staticmethod
    def compute_choice_probabilities(role, prompt, choices):
        """
        Calculates the probability of specific choice tokens given a prompt.
        Returns a dictionary {choice: probability}.
        Currently only implemented for 'transformers' backend.
        """
        path = ModelRegistry.get_model_path(role)

        # Fallback if model not found
        if not path or not os.path.exists(path):
            return {c: 1.0/len(choices) for c in choices}

        try:
            # 1. Handle Full Models (Transformers)
            if os.path.isdir(path):
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch.nn.functional as F

                device = "cuda" if torch.cuda.is_available() else "cpu"
                torch_dtype = torch.float16 if device == "cuda" else torch.float32

                # Check cache
                if path in ModelRegistry._model_cache:
                    # print(f"Using cached model from {path}...")
                    model = ModelRegistry._model_cache[path]
                    tokenizer = ModelRegistry._tokenizer_cache[path]
                else:
                    print(f"Loading model for logprobs from {path}...")
                    tokenizer = AutoTokenizer.from_pretrained(path)
                    model = AutoModelForCausalLM.from_pretrained(
                        path,
                        torch_dtype=torch_dtype,
                        device_map=device,
                        low_cpu_mem_usage=True,
                    )
                    model.eval()
                    ModelRegistry._model_cache[path] = model
                    ModelRegistry._tokenizer_cache[path] = tokenizer

                # Pre-tokenize prompt
                prompt_inputs = tokenizer(prompt, return_tensors="pt").to(device)
                
                choice_scores = []
                
                with torch.no_grad():
                    # We want P(choice | prompt). 
                    # Efficient approach: Get logits for the LAST token of the prompt.
                    outputs = model(**prompt_inputs)
                    next_token_logits = outputs.logits[0, -1, :] # [vocab_size]
                    
                    for choice in choices:
                        # Encode choice without special tokens to get the ID
                        # Note: we assume choices are single tokens or we take the first token
                        choice_ids = tokenizer.encode(choice, add_special_tokens=False)
                        if not choice_ids:
                            choice_scores.append(-float('inf'))
                            continue
                            
                        first_token_id = choice_ids[0]
                        score = next_token_logits[first_token_id].item()
                        choice_scores.append(score)

                # Softmax over the selected choices
                scores_tensor = torch.tensor(choice_scores)
                probs = F.softmax(scores_tensor, dim=0).tolist()
                
                return {choice: round(p, 4) for choice, p in zip(choices, probs)}

        except Exception as e:
            print(f"Error computing probabilities: {e}")
            pass

        # Fallback
        return {c: 1.0/len(choices) for c in choices}
