import logging
import os
from src.config import Settings
from src.ai_assistant import AIAssistant

logger = logging.getLogger(__name__)

class EntrepreneurAgent:
    def __init__(self, config: Settings):
        self.config = config
        self.ai = AIAssistant(config)
        self.ideas_file = "data/ideas.md"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.ideas_file):
            with open(self.ideas_file, "w", encoding="utf-8") as f:
                f.write("# 💡 Clawdbot Project Ideas\n\n")

    def brainstorm_idea(self, topic: str = None) -> str:
        """Generates a business idea using AI."""
        logger.info(f"Brainstorming idea... Topic: {topic or 'General'}")
        
        system_prompt = (
            "You are a visionary entrepreneur, product manager, and tech investor. "
            "Your goal is to generate high-potential, actionable project ideas that can generate revenue. "
            "Focus on: AI Agents, SaaS, Automation, Niche Micro-SaaS, or Web3. "
            "Be specific, not generic."
        )
        
        user_prompt = (
            f"Generate a unique project idea{' related to ' + topic if topic else ''}. "
            "Format exactly like this:\n"
            "**🚀 Project Name**: [Name]\n"
            "**💡 Concept**: [One clear sentence]\n"
            "**💰 Monetization**: [How it makes money]\n"
            "**🛠️ MVP**: [3 bullet points to build v1]"
        )

        idea = self.ai.ask_gpt(system_prompt, user_prompt)
        
        if idea:
            self.save_idea(idea)
            return idea
        return "I tried to think of an idea, but my neural networks were foggy. Try again?"

    def save_idea(self, idea_text: str):
        """Appends the idea to the storage file."""
        try:
            with open(self.ideas_file, "a", encoding="utf-8") as f:
                f.write(f"\n---\n{idea_text}\n")
        except Exception as e:
            logger.error(f"Failed to save idea: {e}")

    def list_ideas(self) -> str:
        """Returns a summary of saved ideas."""
        if not os.path.exists(self.ideas_file):
            return "No ideas saved yet."
            
        with open(self.ideas_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        titles = [line.strip().replace("**🚀 Project Name**:", "").strip() 
                  for line in lines if "**🚀 Project Name**" in line]
        
        if not titles:
            return "No structured ideas found in the file."
            
        return "📂 **Saved Projects:**\n" + "\n".join([f"• {t}" for t in titles])
