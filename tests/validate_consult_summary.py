import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.consult import ConsultStrategy

async def test_summary():
    print("Testing Consultation Summarization...")
    strategy = ConsultStrategy()
    
    # Mock transcript (simulating a doctor-patient interaction)
    mock_transcript = """
    Dtoctor: Good morning, how can I help you today?
    Patient: I've been having a persistent headache for the last 3 days, and some dizziness.
    Doctor: Have you experienced any nausea or vomiting?
    Patient: A little bit of nausea yesterday, but no vomiting.
    Doctor: Any engaging in strenuous activity?
    Patient: No, mostly resting.
    Doctor: I'll prescribe some ibuprofen and I want you to monitor your blood pressure.
    """
    
    print(f"Input Transcript:\n{mock_transcript}\n")
    
    try:
        # 1. Generate Note
        print("Generating Clinical Note...")
        result = strategy.generate_clinical_note(mock_transcript)
        
        if result['status'] == 'success':
            note = result['data']['note']
            print("\nGenerated Note:")
            print("-" * 40)
            print(note)
            print("-" * 40)
            
            # Check for key sections
            if "Key Discussion Points" in note or "Important Factors" in note:
                 print("\nSUCCESS: Summary contains 'Important Factors' section.")
            else:
                 print("\nWARNING: Summary MIGHT be missing 'Important Factors' section.")
                 
            # 2. Save Note
            print("\nSaving to Vault...")
            save_result = strategy.save_clinical_note(note)
            if save_result['status'] == 'success':
                 print(f"SUCCESS: Note saved with ID {save_result['data']['id']}")
            else:
                 print(f"FAILURE: Could not save note. {save_result['message']}")
                 
        else:
            print(f"FAILURE: Generation failed. {result.get('message')}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_summary())
