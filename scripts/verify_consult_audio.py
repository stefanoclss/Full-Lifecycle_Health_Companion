
import asyncio
import json
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.consult import ConsultStrategy
from model_registry import ModelRegistry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ConsultVerification")

async def test_consult_flow():
    strategy = ConsultStrategy()
    
    logger.info("--- 1. Testing Get Audio ---")
    audio_result = strategy.process_action({"action": "get_audio"})
    logger.info(f"Audio Result: {json.dumps(audio_result, indent=2)}")
    
    if audio_result["status"] != "success":
        logger.error("Get audio failed")
        return

    logger.info("--- 2. Testing Transcription (Mocking if model not loaded, or real) ---")
    # This might take time if model loads
    transcribe_result = strategy.process_action({"action": "transcribe"})
    
    # Don't print full transcript if huge
    if transcribe_result["status"] == "success":
        text = transcribe_result["data"]["text"]
        logger.info(f"Transcription Success. Length: {len(text)} chars")
        logger.info(f"Preview: {text[:200]}...")
    else:
        logger.error(f"Transcription Failed: {transcribe_result.get('message')}")
        return

    logger.info("--- 3. Testing Note Generation ---")
    transcript = transcribe_result["data"]["text"]
    note_result = strategy.process_action({"action": "generate_note", "payload": {"transcript": transcript}})
    
    if note_result["status"] == "success":
        note = note_result["data"]["note"]
        logger.info(f"Note Generated:\n{note}")
    else:
        logger.error(f"Note Gen Failed: {note_result.get('message')}")
        return

    logger.info("--- 4. Testing Save Note ---")
    save_result = strategy.process_action({"action": "save_note", "payload": {"note": note}})
    logger.info(f"Save Result: {save_result}")

if __name__ == "__main__":
    asyncio.run(test_consult_flow())
