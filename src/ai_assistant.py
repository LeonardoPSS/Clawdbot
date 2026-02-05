import logging
import json
import urllib.request
import urllib.parse
from typing import Optional, Dict
from src.config import Settings

import os

logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self, config: Settings):
        self.config = config
        self.knowledge_path = "data/user_knowledge.md"
        self.api_key = ""
        if config.secrets and config.secrets.openai:
            # In secrets.yaml: 
            # openai:
            #   api_key: "..."
            self.api_key = config.secrets.openai.get("api_key", "")
        
            self.api_key = config.secrets.openai.get("api_key", "")
        
        # Load model from config or default to gpt-4o
        self.model = getattr(config, "ai", {}).get("model", "gpt-4o") if hasattr(config, "ai") else "gpt-4o"
        logger.info(f"🧠 AI Assistant initialized with model: {self.model}")
        
        self.url = "https://api.openai.com/v1/chat/completions"
        self.last_429_time = 0
        self.cooldown_seconds = 300 # Wait 5 minutes after a 429

    def _load_persona(self) -> str:
        if os.path.exists(self.knowledge_path):
            try:
                with open(self.knowledge_path, "r", encoding="utf-8") as f:
                    return f.read()
            except: pass
        return ""

    def ask_gpt(self, system_prompt: str, user_prompt: str, incorporate_persona: bool = False) -> Optional[str]:
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

        if incorporate_persona:
            persona_text = self._load_persona()
            if persona_text:
                system_prompt += f"\n\n[USER PERSONA & KNOWLEDGE]\nAct as if you are the user described below, or align your decisions with their preferences:\n{persona_text}"

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
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if "429" in str(e):
                logger.error(f"OpenAI API Quota/Rate Limit reached (429). Cooling down for {self.cooldown_seconds/60} minutes.")
                self.last_429_time = time.time()
            elif "timed out" in str(e).lower():
                logger.error("OpenAI API request timed out.")
            else:
                logger.error(f"Error calling OpenAI API: {e}")
            return None

    def ask_gpt_with_history(self, system_prompt: str, history: list, incorporate_persona: bool = False) -> Optional[str]:
        """Sends a request to OpenAI using a list of messages for context."""
        if not self.api_key: return None
        
        # Cooldown check
        import time
        if time.time() - self.last_429_time < self.cooldown_seconds:
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        messages = [{"role": "system", "content": system_prompt}]
        
        if incorporate_persona:
            persona_text = self._load_persona()
            if persona_text:
                messages[0]["content"] += f"\n\n[USER PERSONA & KNOWLEDGE]\n{persona_text}"

        # Append history (ensure it's formatted correctly)
        messages.extend(history)

        messages.extend(history)

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5 
        }

        try:
            req = urllib.request.Request(self.url, data=json.dumps(data).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=40) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Error in smart chat: {e}")
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

    def ask_gpt_vision(self, prompt: str, base64_image: str) -> Optional[str]:
        """Sends an image to GPT-4o for analysis."""
        if not self.api_key: return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }

        try:
            req = urllib.request.Request(self.url, data=json.dumps(data).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Error in Vision API: {e}")
            return f"❌ Vision Error: {e}"

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribes audio using OpenAI Whisper API."""
        if not self.api_key: return "⚠️ API Key missing."
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
            # Content-Type is multipart/form-data, requests lib handles this better than urllib
        }
        
        # Using requests here because multipart upload with urllib is painful
        try:
            import requests
            with open(audio_path, "rb") as f:
                files = {
                    "file": (os.path.basename(audio_path), f, "audio/mpeg"),
                    "model": (None, "whisper-1")
                }
                response = requests.post(url, headers=headers, files=files)
                result = response.json()
                return result.get("text", f"❌ Error: {result}")
        except Exception as e:
            logger.error(f"Whisper Error: {e}")
            return f"❌ Transcription Error: {e}"

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
        except Exception as e:
            logger.warning(f"Failed to parse compatibility score: {e}")
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
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["data"][0]["url"]
        except Exception as e:
            logger.error(f"Error generating image with DALL-E: {e}")
            return None

