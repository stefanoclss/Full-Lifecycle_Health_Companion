
import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.medical_vault import MedicalVault, MedicalEntry

def extract_note(note_id):
    vault = MedicalVault()
    session = vault.Session()
    try:
        entry = session.query(MedicalEntry).filter(MedicalEntry.id == note_id).first()
        if entry:
            print(f"\n--- Clinical Note (ID: {entry.id}) ---")
            print(f"Category: {entry.category}")
            print(f"Timestamp: {entry.timestamp}")
            print(f"Tags: {entry.tags}\n")
            
            try:
                content = json.loads(entry.content)
                print(json.dumps(content, indent=2))
            except:
                print(entry.content)
            
            print("\n-----------------------------------\n")
        else:
            print(f"Note with ID {note_id} not found.")
    finally:
        session.close()

if __name__ == "__main__":
    extract_note(11)
