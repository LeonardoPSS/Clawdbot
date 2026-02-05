import time
import logging
from src.neo_trade_bot import NeoTradeBot
from src.growth_engine import GrowthEngine
from src.config import load_config
from src.telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO)

def nexara_autopilot_cycle():
    print("🤖 Nexara Autopilot: Iniciando ciclo diário...")
    config = load_config("config/settings.yaml")
    
    # 1. Trading
    trader = NeoTradeBot()
    trader.run_cycle()
    print(f"💹 NeoTrade: Ciclo concluído. Saldo: ${trader.wealth['balance']:.2f}")
    
    # 2. Daily Insight / Content Arbitrage
    # (Em uma versão real, buscaríamos o URL aqui)
    print("📺 Viral Transmuter: Buscando tendências...")
    
    # 3. Micro-SaaS Evolution
    growth = GrowthEngine(config)
    print("🏗️ SaaS Factory: Pesquisando próxima oportunidade...")
    # Se não houver scraper, cria um
    import os
    if not os.path.exists("src/skills/maps_scraper.py"):
        print("🧬 Mutando: Criando 'Google Maps Scraper'...")
        instruction = "Um script em Python usando Playwright que busca empresas no Google Maps por categoria e cidade, extraindo Nome, Telefone e Site para um CSV."
        growth.generate_skill(instruction)
    
    print("✅ Nexara Autopilot: Ciclo finalizado com sucesso.")

if __name__ == "__main__":
    nexara_autopilot_cycle()
