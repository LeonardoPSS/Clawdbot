import os
import json
import logging
import requests
from src.config import load_config

logger = logging.getLogger("ProjectForge")

class ProjectForge:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = load_config(config_path)
        self.openai_api_key = self.config.secrets.openai.get("api_key") if self.config.secrets else None
        self.projects_dir = r"c:\Users\leona\Downloads\ClawdProjects"
        self.trends_path = "data/market_trends.json"
        
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)

    def _generate_idea(self):
        if not os.path.exists(self.trends_path):
            return {"name": "TestBot", "description": "A placeholder project.", "files": []}

        with open(self.trends_path, "r", encoding="utf-8") as f:
            trends = json.load(f)

        # Use OpenAI to pick the best gap and define a project
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        
        system_prompt = "You are a Senior Product Architect. Analyze market trends and propose a simple, high-impact 100% autonomous MVP (Python or React). Output ONLY JSON."
        user_prompt = f"Trends: {json.dumps(trends[:10])}\n\nTask: Return a JSON with 'name', 'description', 'primary_stack' and 'file_structure' (list of paths)."
        
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": { "type": "json_object" }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            res_json = response.json()
            if "choices" in res_json:
                return res_json["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI error: {res_json}")
                return None
        except Exception as e:
            logger.error(f"Idea generation failed: {e}")
            return None

    def build_project(self):
        logger.info("🛠️ Forge is heating up... Analyzing market leads...")
        idea_json = self._generate_idea()
        if not idea_json: return

        idea = json.loads(idea_json)
        project_name = idea.get("name", "AutoProject").replace(" ", "_")
        project_path = os.path.join(self.projects_dir, project_name)
        
        os.makedirs(project_path, exist_ok=True)
        logger.info(f"🚀 Incubating project: {project_name}")

        # Core logic: In a real scenario, this would loop to generate each file.
        # For the MVP of the Forge, we'll create the structure and the PRD.
        with open(os.path.join(project_path, "PRD.md"), "w", encoding="utf-8") as f:
            f.write(f"# Project: {project_name}\n\n## Description\n{idea.get('description')}\n\n## Stack\n{idea.get('primary_stack')}")

        # Save status for Dashboard
        with open("data/forge_status.json", "w", encoding="utf-8") as f:
            json.dump({"current_project": project_name, "status": "Boilerplate Built", "path": project_path}, f)

        return project_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    forge = ProjectForge()
    forge.build_project()
