import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.home_triage import HomeTriageStrategy
from data.medical_vault import vault

def test_manual_save():
    strategy = HomeTriageStrategy()
    
    print("1. Running Analysis (Should NOT auto-save)...")
    # This queries DB & AI. To save time/cost, we can mock the AI part or just run it.
    # Let's run it for real to be sure.
    analysis_result = strategy.analyze_trends()
    
    if analysis_result['status'] != 'success':
        print("❌ Analysis failed")
        return

    print("✅ Analysis complete.")
    
    # Check if it was saved (it shouldn't be)
    # We can't easily check 'it wasn't saved' without knowing the previous count, 
    # but we can rely on verifying the explicit save works.
    
    payload = analysis_result['data']
    print(f"2. Manually Saving Payload ({len(payload)} items)...")
    
    save_result = strategy.save_analysis(payload)
    
    if save_result['status'] == 'success':
        entry_id = save_result['data']['id']
        print(f"✅ Save successful! Entry ID: {entry_id}")
        
        # Verify in Vault
        entries = vault.get_entries(limit=1)
        if entries and entries[0]['id'] == entry_id:
            print(f"✅ Verified in Vault: {entries[0]['category']} at {entries[0]['timestamp']}")
            if "Manual" in entries[0]['tags']:
                print("✅ Tagged as 'Manual'")
            else:
                print("❌ Missing 'Manual' tag")
        else:
            print("❌ Entry not found in Vault")
    else:
        print(f"❌ Save failed: {save_result['message']}")

if __name__ == "__main__":
    test_manual_save()
