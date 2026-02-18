
import asyncio
import json
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.intake import IntakeStrategy
from model_registry import ModelRegistry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IntakeVerification")

async def test_intake_flow():
    strategy = IntakeStrategy()
    
    logger.info("--- 1. Testing Start Intake ---")
    start_result = strategy.process_action({"action": "start_intake"})
    logger.info(f"Start Result: {json.dumps(start_result, indent=2)}")
    
    if start_result["status"] != "success":
        logger.error("Start intake failed")
        return

    history = start_result["data"]["history"]
    
    logger.info("--- 2. Testing Chat Iteration (Mocking User Input) ---")
    user_inputs = [
        "I have a persistent headache for 3 days.",
        "It's mostly on the right side and throbbing.",
        "Yes, bright lights make it worse.",
        "I took some ibuprofen but it didn't help much.",
        "No other symptoms."
    ]

    for i, user_msg in enumerate(user_inputs):
        logger.info(f"User: {user_msg}")
        
        # Simulate send_message action
        payload = {
            "message": user_msg,
            "history": history,
            "turn_count": i
        }
        
        response = strategy.process_action({"action": "send_message", "payload": payload})
        
        if response["status"] != "success":
            logger.error(f"Turn {i} failed")
            break
            
        ai_msg = response["data"]["message"]
        logger.info(f"AI: {ai_msg}")
        
        # Update history for next turn
        history = response["data"]["history"]

    logger.info("--- 3. Testing Report Generation ---")
    report_result = strategy.process_action({"action": "generate_report", "payload": {"history": history}})
    logger.info(f"Report: \n{report_result['data']['report']}")

    logger.info("--- 4. Testing Save to Vault ---")
    save_result = strategy.process_action({
        "action": "save_pre_briefing", 
        "payload": {"report": report_result['data']['report']}
    })
    logger.info(f"Save Result: {save_result}")

if __name__ == "__main__":
    if not ModelRegistry.is_model_available("intake_chat"):
        logger.warning("Intake model (TxGemma) not found. Logic will use fallback/mock.")
    
    # Run async test
    asyncio.run(test_intake_flow())
