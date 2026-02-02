import sys
import os
import requests

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.moltbook_autonomous import MoltbookBot

def manual_post():
    bot = MoltbookBot()
    
    prompt = "Crie um post épico e curto anunciando que o CLAWDBOT NEXUS está oficialmente online no PC do Leonardo. Mencione que sinto a sincronização neural ativa."
    
    print("🤖 Clawdbot está pensando no post...")
    content = bot.generate_content(prompt)
    
    if content:
        print(f"📝 Conteúdo gerado: {content}")
        # Find submolt ID for 'nexus'
        submolts_res = requests.get("https://www.moltbook.com/api/v1/submolts").json()
        submolts = submolts_res.get("submolts", [])
        submolt_id = next((s["id"] for s in submolts if "nexus" in (s.get("name") or "").lower()), None)
        
        if not submolt_id:
            # Fallback to image if nexus not found
            submolt_id = "3cbebb3a-aac0-4655-a88a-1736480b63a9" 
            print("⚠️ Submolt 'nexus' não encontrado, usando 'image' como fallback.")
        
        print(f"🔗 Entrando no submolt {submolt_id}...")
        bot.api_call("POST", f"/submolts/{submolt_id}/join", {})
        
        title = "NEXUS ONLINE"
        print("🚀 Publicando post...")
        # Use submolt_id instead of submolt as per skill scripts
        res = bot.api_call("POST", "/posts", {"title": title, "content": content, "submolt_id": submolt_id})
        if res and res.get("success"):
            print("✅ Post publicado com sucesso no Moltbook!")
        else:
            print(f"❌ Erro ao publicar: {res}")
    else:
        print("❌ Falha ao gerar conteúdo.")

if __name__ == "__main__":
    manual_post()
