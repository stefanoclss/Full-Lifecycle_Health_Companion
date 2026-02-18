import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_registry import ModelRegistry

def debug_cardio():
    prompt = (
        "Analyze user cardio load.\n"
        "Data: Max HR 191, Avg HR 82.0.\n"
        "Classify strictly as one of: [Bradycardic, Normal, Elevated, Strain].\n"
        "Classification:\n"
    )
    
    print("--- Prompt ---")
    print(prompt)
    # print("--- Generating Raw Output ---")
    # output = ModelRegistry.run_inference("consult_reasoning", prompt)
    # print(f"Raw Output: '{output}'")

    print("\n--- Computing Logprobs ---")
    choices = ["Bradycardic", "Normal", "Elevated", "Strain"]
    probs = ModelRegistry.compute_choice_probabilities("consult_reasoning", prompt, choices)
    print(f"Probs: {probs}")

if __name__ == "__main__":
    debug_cardio()
