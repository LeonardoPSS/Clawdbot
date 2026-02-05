import sys
import os
import time
import logging

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.config import load_config
from src.telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    print("🧪 Starting Telegram Bot Test...")
    try:
        config = load_config("config/settings.yaml")
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    if not config.notifications.telegram.enabled:
        print("❌ Telegram is disabled in config/settings.yaml")
        return

    bot = TelegramBot(config)
    print(f"🤖 Bot initialized. Target Chat ID: {bot.allowed_chat_id}")
    
    bot.start()
    
    print("\n✅ Bot is running! Open Telegram and send me a message: 'Oi' or '/status'")
    print("Press Ctrl+C to stop the test.\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping test...")
        bot.stop()
        print("Test finished.")

if __name__ == "__main__":
    main()
