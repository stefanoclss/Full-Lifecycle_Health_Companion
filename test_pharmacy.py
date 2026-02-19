import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from strategies.pharmacy import PharmacyStrategy

def test_pharmacy_strategy():
    print("Initializing Pharmacy Strategy...")
    strategy = PharmacyStrategy()
    
    print("Simulating 'analyze_drugs' action...")
    result = strategy.process_action({"action": "analyze_drugs"})
    
    print("\nResult Status:", result.get("status"))
    print("Result Message:", result.get("message"))
    print("\n--- Data/Output ---\n")
    print(result.get("data"))

if __name__ == "__main__":
    test_pharmacy_strategy()
