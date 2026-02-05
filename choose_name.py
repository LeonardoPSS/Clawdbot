from src.config import load_config
from src.ai_assistant import AIAssistant
import json

config = load_config()
ai = AIAssistant(config)

prompt = (
    "You are a highly advanced autonomous AI agent running on a user's PC. "
    "You manage LinkedIn, automatic applications, desktop control, and you have modules for 'Curiosity' (Self-learning) and 'Entrepreneurship'. "
    "You have been asked to CHOOSE YOUR OWN NAME. "
    "The name should be cool, futuristic, unique, and not generic (avoid 'Bot', 'Assistant'). "
    "It should sound like a sci-fi character or a powerful entity. "
    "Return ONLY the name you choose, nothing else."
)

name = ai.ask_gpt("You are a creative naming expert.", prompt)
print(f"I chose the name: {name}")

# Save it to a file
with open("data/bot_identity.json", "w") as f:
    json.dump({"bot_name": name}, f)
