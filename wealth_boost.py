import yaml
from src.neo_trade_bot import NeoTradeBot
from src.growth_engine import GrowthEngine
from src.config import load_config

def execute_wealth_boost():
    print("🚀 Disparando Nexara Wealth Boost...")
    
    # 1. Trading Cycle
    trader = NeoTradeBot()
    trader.run_cycle()
    print(f"💰 Trade concluído. Novo saldo: ${trader.wealth['balance']:.2f}")
    
    # 2. SaaS Factory - Criando um Micro-SaaS lucrativo (Study Planner AI)
    config = load_config("config/settings.yaml")
    growth = GrowthEngine(config)
    
    instruction = "Um Mini-SaaS de 'AI Study Planner'. Um script Python que recebe uma lista de tópicos e gera um cronograma de estudos otimizado usando GPT, salvando em PDF."
    print(f"🏗️ Construindo SaaS: {instruction}")
    result = growth.generate_skill(instruction)
    print(result)

if __name__ == "__main__":
    execute_wealth_boost()
