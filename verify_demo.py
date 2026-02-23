import os
import sys

# Ensure demo mode is set
os.environ["DEMO_MODE"] = "True"

from strategies.home_triage import HomeTriageStrategy
from strategies.intake import IntakeStrategy
from strategies.consult import ConsultStrategy
from strategies.pharmacy import PharmacyStrategy

def test_strategy(name, strategy_cls, action, payload=None):
    print(f"\n--- Testing {name} -> {action} ---")
    strategy = strategy_cls()
    data = {"action": action}
    if payload:
        data["payload"] = payload
        
    result = strategy.process_action(data)
    
    print(f"Status: {result.get('status')}")
    message = result.get('message', '')
    print(f"Message: {message}")
    
    if "(DEMO)" in message or "Demo" in message or "DEMO" in str(result):
        # Pharmacy returns true in alert and "Analysis Complete (DEMO)"
        # Consult doesn't have a message but returns just "status" and "data" with "note".
        print("✅ DEMO MODE ACTIVATED")
    elif "consult" in name and "note" in result.get("data", {}):
         print("✅ DEMO MODE ACTIVATED (Consult Note loaded)")
    else:
        print("❌ DEMO MODE NOT DETECTED or EMPTY VAULT")
        print(f"Result: {result}")

if __name__ == "__main__":
    test_strategy("Home Triage", HomeTriageStrategy, "analyze_trends")
    test_strategy("Intake", IntakeStrategy, "generate_report", payload={"history": []})
    test_strategy("Consult", ConsultStrategy, "generate_note", payload={"transcript": "test"})
    test_strategy("Pharmacy", PharmacyStrategy, "analyze_drugs")
