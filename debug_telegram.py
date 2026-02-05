import os
import sys
from src.config import load_config
from src.telegram_bot import TelegramBot
import logging

# Setup logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_telegram():
    print("--- TESTING TELEGRAM CONNECTION ---")
    try:
        config = load_config("config/settings.yaml")
        print("Config loaded.")
        
        if not config.secrets or not config.secrets.telegram:
            print("❌ No secrets/telegram config found!")
            return

        token = config.secrets.telegram.get("bot_token", "")
        chat_id = config.secrets.telegram.get("chat_id", "")
        
        print(f"Token present: {'Yes' if token else 'No'} ({token[:5]}...)")
        print(f"Chat ID present: {'Yes' if chat_id else 'No'} ({chat_id})")

        bot = TelegramBot(config)
        print("TelegramBot initialized.")
        
        print("Attempting to send startup message...")
        bot.send_message(str(chat_id), "🧪 TEST: Clawdbot Debug Protocol Initiated.")
        print("Message sent (fire and forget). Check your phone.")
        
        print("Attempting to get updates...")
        updates = bot._get_updates(offset=0, timeout=5)
        print(f"Updates received: {len(updates)}")
        for u in updates:
            print(f"Update: {u}")
            
    except Exception as e:
        print(f"❌ CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_telegram()
