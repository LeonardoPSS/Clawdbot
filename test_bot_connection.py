#!/usr/bin/env python3
"""
Script de diagnóstico para testar a conexão do bot do Telegram
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def test_bot_connection():
    """Testa se o bot está configurado corretamente"""
    print("[*] Testando conexao com o Telegram Bot API...\n")
    
    if not TELEGRAM_BOT_TOKEN:
        print("[X] ERRO: TELEGRAM_BOT_TOKEN nao encontrado no .env")
        return False
    
    if not TELEGRAM_CHAT_ID:
        print("[X] ERRO: TELEGRAM_CHAT_ID nao encontrado no .env")
        return False
    
    print(f"[OK] Token encontrado: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"[OK] Chat ID encontrado: {TELEGRAM_CHAT_ID}\n")
    
    # Testar getMe
    print("[*] Testando getMe...")
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            bot_info = data.get("result", {})
            print(f"[OK] Bot conectado com sucesso!")
            print(f"   Nome: {bot_info.get('first_name')}")
            print(f"   Username: @{bot_info.get('username')}")
            print(f"   ID: {bot_info.get('id')}\n")
        else:
            print(f"[X] Erro na API: {data}")
            return False
    except Exception as e:
        print(f"[X] Erro ao conectar: {e}")
        return False
    
    # Testar getUpdates
    print("[*] Testando getUpdates (ultimas mensagens)...")
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            updates = data.get("result", [])
            print(f"[OK] {len(updates)} atualizacoes encontradas")
            
            if updates:
                last_update = updates[-1]
                message = last_update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id", "")
                
                print(f"   Ultima mensagem: '{text}'")
                print(f"   Chat ID: {chat_id}")
                
                if str(chat_id) != str(TELEGRAM_CHAT_ID):
                    print(f"   [!] AVISO: Chat ID diferente do configurado!")
                    print(f"   Configurado: {TELEGRAM_CHAT_ID}")
                    print(f"   Recebido: {chat_id}")
            print()
        else:
            print(f"[X] Erro na API: {data}")
            return False
    except Exception as e:
        print(f"[X] Erro ao buscar updates: {e}")
        return False
    
    # Enviar mensagem de teste
    print("[*] Enviando mensagem de teste...")
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": "Teste de conexao do bot - Tudo funcionando!",
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            print("[OK] Mensagem enviada com sucesso!")
            print(f"   Message ID: {data.get('result', {}).get('message_id')}\n")
        else:
            print(f"[X] Erro ao enviar mensagem: {data}")
            return False
    except Exception as e:
        print(f"[X] Erro ao enviar mensagem: {e}")
        return False
    
    print("=" * 50)
    print("[OK] TODOS OS TESTES PASSARAM!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = test_bot_connection()
    sys.exit(0 if success else 1)
