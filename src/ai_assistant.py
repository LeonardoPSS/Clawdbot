import logging
import json
import urllib.request
import urllib.parse
from typing import Optional, Dict
from src.config import Settings

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self, config: Settings):
        self.config = config
        self.api_key = ""
        if config.secrets and config.secrets.openai:
            # In secrets.yaml: 
            # openai:
            #   api_key: "..."
            self.api_key = config.secrets.openai.get("api_key", "")
        
        self.model = "gpt-4o-mini" # Faster and cheaper, less likely to hit 429
        self.url = "https://api.openai.com/v1/chat/completions"
        self.last_429_time = 0
        self.cooldown_seconds = 300 # Wait 5 minutes after a 429

    def ask_gpt(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Sends a request to OpenAI Chat Completion API with cooldown handling."""
        if not self.api_key:
            return None

        # Check for cooldown
        import time
        if time.time() - self.last_429_time < self.cooldown_seconds:
            logger.warning("AI features are on cooldown due to rate limits. Skipping request.")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3 
        }

        try:
            req = urllib.request.Request(self.url, data=json.dumps(data).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if "429" in str(e):
                logger.error(f"OpenAI API Quota/Rate Limit reached (429). Cooling down for {self.cooldown_seconds/60} minutes.")
                self.last_429_time = time.time()
            else:
                logger.error(f"Error calling OpenAI API: {e}")
            return None

    def get_answer_for_question(self, question_text: str, resume_context: str) -> Optional[str]:
        """Generates an answer for a specific form question based on the resume."""
        system_prompt = (
            "You are a helpful job application assistant. Using the provided resume details, "
            "provide a short, direct answer to the form question. "
            "If it's a 'How many years' question, respond only with a number. "
            "If it's a 'Why us' question, write 2-3 professional sentences. "
            "Language must match the question (Portuguese or English)."
        )
        
        user_prompt = f"Resume Context: {resume_context}\n\nQuestion: {question_text}\n\nAnswer:"
        
        logger.info(f"Asking GPT for answer to: {question_text[:50]}...")
        return self.ask_gpt(system_prompt, user_prompt)

    def evaluate_compatibility(self, job_description: str, resume_context: str) -> int:
        """Evaluates job compatibility score (0-100) using AI."""
        system_prompt = (
            "You are an expert HR recruiter. Compare the Job Description and the Resume. "
            "Return ONLY a whole number from 0 to 100 representing the compatibility score."
        )
        
        user_prompt = f"Resume: {resume_context}\n\nJob Description: {job_description}\n\nScore:"
        
        result = self.ask_gpt(system_prompt, user_prompt)
        try:
            return int(result) if result and result.isdigit() else 50
        except:
            return 50

    def generate_image(self, prompt: str) -> Optional[str]:
        """Generates an image using OpenAI's DALL-E 3 and returns the URL."""
        if not self.api_key:
            return None

        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }

        try:
            logger.info(f"Generating image with DALL-E 3... Prompt: {prompt[:50]}...")
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["data"][0]["url"]
        except Exception as e:
            logger.error(f"Error generating image with DALL-E: {e}")
            return None

