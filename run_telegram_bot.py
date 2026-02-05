#!/usr/bin/env python3
"""
Script simplificado para rodar APENAS o bot do Telegram
Sem browser, sem automação de jobs - apenas o chatbot
"""
import logging
import sys
import time
from src.config import load_config
from src.telegram_bot import TelegramBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("telegram_bot.log", mode="a", encoding="utf-8")
    ]
)
logger = logging.getLogger("TelegramBotOnly")

def main():
    logger.info("=" * 60)
    logger.info("Iniciando Bot do Telegram (Modo Standalone)")
    logger.info("=" * 60)
    
    # Load config
    try:
        config = load_config("config/settings.yaml")
    except Exception as e:
        logger.critical(f"Erro ao carregar config: {e}")
        return
    
    # Initialize Telegram Bot
    telegram_bot = TelegramBot(config)
    
    # Start the bot
    telegram_bot.start()
    logger.info("Bot do Telegram iniciado com sucesso!")
    logger.info(f"Bot Name: {telegram_bot.bot_name}")
    logger.info(f"Chat ID: {telegram_bot.allowed_chat_id}")
    logger.info("")
    logger.info("Aguardando mensagens... (Ctrl+C para parar)")
    logger.info("=" * 60)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nParando bot...")
        telegram_bot.stop()
        logger.info("Bot encerrado.")

if __name__ == "__main__":
    main()
