import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_registry import ModelRegistry

def debug_cardio_chat():
    # Gemma chat template
    user_msg = (
        "Analyze user cardio load.\n"
        "Data: Max HR 191, Avg HR 82.0.\n"
        "Classify strictly as one of: [Bradycardic, Normal, Elevated, Strain].\n"
        "Return ONLY the classification label."
    )
    
    prompt = f"<start_of_turn>user\n{user_msg}<end_of_turn>\n<start_of_turn>model\n"
    
    print("--- Prompt ---")
    print(prompt)

    print("\n--- Computing Logprobs ---")
    choices = ["Bradycardic", "Normal", "Elevated", "Strain"]
    probs = ModelRegistry.compute_choice_probabilities("consult_reasoning", prompt, choices)
    print(f"Probs: {probs}")

if __name__ == "__main__":
    debug_cardio_chat()
