import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.home_triage import HomeTriageStrategy

def test_analyze_trends():
    print("Initializing HomeTriageStrategy...")
    strategy = HomeTriageStrategy()
    
    print("Calling analyze_trends()...")
    # This will query the DB and attempt to load the model
    result = strategy.analyze_trends()
    
    print("\n--- Result ---")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    
    print("\n--- Metrics ---")
    print(json.dumps(result.get("metrics"), indent=2))
    
    print("\n--- Dimensional Analysis ---")
    data = result.get('data', [])
    if isinstance(data, list):
        print(f"{'Dimension':<30} | {'Status':<15} | {'Severity':<10} | {'Conf':<6}")
        print("-" * 70)
        for item in data:
            print(f"{item.get('dimension', 'N/A'):<30} | {item.get('status', 'N/A'):<15} | {item.get('severity', 'N/A'):<10} | {item.get('confidence', 0):.2f}")
    else:
        print(data)

if __name__ == "__main__":
    test_analyze_trends()
