import os
import json
import logging
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import requests
import asyncio
import subprocess

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_DIR = r"c:\Users\leona\Downloads\AntigravityJobBot"
KNOWLEDGE_PATH = os.path.join(BOT_DIR, "data", "user_knowledge.md")
TASKS_PATH = os.path.join(BOT_DIR, "data", "mission.md")
MOLTBOOK_CREDS_PATH = os.path.expanduser("~/.config/moltbook/credentials.json")
TRENDS_PATH = os.path.join(BOT_DIR, "data", "market_trends.json")
FORGE_STATUS_PATH = os.path.join(BOT_DIR, "data", "forge_status.json")
CHAT_HISTORY_PATH = os.path.join(BOT_DIR, "data", "dashboard_chat.json")
WEALTH_PATH = os.path.join(BOT_DIR, "data", "neural_wealth.json")
TRADE_HISTORY_PATH = os.path.join(BOT_DIR, "data", "trade_history.json")

class BotStatus(BaseModel):
    cpu_percent: float
    ram_percent: float
    uptime_seconds: float
    is_online: bool

@app.get("/api/identity")
def get_identity():
    if os.path.exists(KNOWLEDGE_PATH):
        with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"content": "# No Knowledge Found\nClawdbot is still learning..."}

@app.get("/api/tasks")
def get_tasks():
    if os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"content": "Tasks file not found."}

@app.get("/api/moltbook/activity")
def get_moltbook_activity():
    try:
        if os.path.exists(MOLTBOOK_CREDS_PATH):
            with open(MOLTBOOK_CREDS_PATH, "r") as f:
                creds = json.load(f)
                api_key = creds.get("api_key")
                
                # Fetch recent posts from the agent
                url = f"https://www.moltbook.com/api/v1/agents/me"
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get(url, headers=headers)
                return response.json()
    except Exception as e:
        return {"error": str(e)}
    return {"error": "Credentials not found"}

@app.get("/api/forge/trends")
def get_trends():
    if os.path.exists(TRENDS_PATH):
        with open(TRENDS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.get("/api/forge/status")
def get_forge_status():
    if os.path.exists(FORGE_STATUS_PATH):
        with open(FORGE_STATUS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"current_project": "None", "status": "Idle"}

@app.post("/api/chat")
async def chat_with_bot(message: dict):
    user_msg = message.get("text", "").lower()
    
    # Load knowledge for context
    context = ""
    if os.path.exists(KNOWLEDGE_PATH):
        with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
            context = f.read()

    # Dynamic response logic based on context and keywords
    if "quem é você" in user_msg or "quem e voce" in user_msg:
        response_text = "Eu sou o Clawdbot, sua extensão neural autônoma. Atualmente, monitoro o Moltbook e o mercado para você."
    elif "faz" in user_msg or "consegue fazer" in user_msg:
        response_text = "Eu gerencio sua presença no Moltbook, aprendo sobre seus interesses (como Brave Search e AI) e posso construir projetos autônomos na 'Forja' baseado no que o Oráculo descobre."
    elif "projeto" in user_msg or "forge" in user_msg:
        response_text = "A Forja está online. Posso iniciar um novo ciclo de incubação assim que você der o comando 'Ignition'."
    elif "status" in user_msg:
        response_text = "Sincronização nominal. Conexão com Moltbook ativa. Coração neural (Vite) operando em 5173."
    else:
        response_text = f"Entendido, Leonardo. Processando sua entrada: '{user_msg}'. Como posso otimizar nosso fluxo agora?"

    chat_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user_msg,
        "bot": response_text
    }

    # Save to history
    history = []
    if os.path.exists(CHAT_HISTORY_PATH):
        try:
            with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except: pass
    
    history.append(chat_entry)
    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history[-50:], f, indent=4) # Keep last 50

    return {"response": response_text}

@app.get("/api/wealth")
def get_wealth():
    if os.path.exists(WEALTH_PATH):
        with open(WEALTH_PATH, "r") as f:
            wealth = json.load(f)
            # Fetch history too
            history = []
            if os.path.exists(TRADE_HISTORY_PATH):
                with open(TRADE_HISTORY_PATH, "r") as fh:
                    history = json.load(fh)
            wealth["history"] = history
            return wealth
    return {"balance": 1000.0, "active_positions": [], "history": []}

@app.get("/api/health")
def get_health():
    # Prime psutil for first run if needed
    psutil.cpu_percent()
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "is_online": True,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/actions/{action_name}")
async def run_action(action_name: str):
    try:
        if action_name == "sync":
            # Start knowledge sync
            subprocess.Popen(["python", "-m", "src.history_observer"], cwd=BOT_DIR)
            return {"status": "Sync triggered"}
        elif action_name == "moltbook":
            # Trigger cycle
            subprocess.Popen(["python", "-m", "src.moltbook_autonomous", "--once"], cwd=BOT_DIR)
            return {"status": "Moltbook cycle triggered"}
        elif action_name == "forge":
            # Trigger market scan and project incubation
            subprocess.Popen(["python", "-m", "src.market_analyst"], cwd=BOT_DIR)
            subprocess.Popen(["python", "-m", "src.project_forge"], cwd=BOT_DIR)
            return {"status": "The Forge is heating up... market scan and incubation triggered"}
        elif action_name == "trade":
            # Trigger NeoTrade cycle
            subprocess.Popen(["python", "-m", "src.neo_trade_bot"], cwd=BOT_DIR)
            return {"status": "NeoTrade cycle initiated. Markets are moving."}
        elif action_name == "linkedin":
            # Trigger LinkedIn full cycle
            subprocess.Popen(["python", "-m", "src.main"], cwd=BOT_DIR)
            return {"status": "LinkedIn Evolution Suite activated. Processing applications and engagement."}
        return {"error": "Unknown action"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
