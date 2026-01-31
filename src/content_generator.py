import logging
import random
import datetime
from typing import Optional, List
from src.ai_assistant import AIAssistant
from src.config import Settings

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Advanced content generation for LinkedIn posts with variety and images."""
    
    def __init__(self, config: Settings):
        self.config = config
        self.ai = AIAssistant(config)
        self.topics = config.linkedin_automation.daily_posts.topics if hasattr(config, 'linkedin_automation') else [
            "Inteligência Artificial",
            "Carreira e Desenvolvimento",
            "Produtividade",
            "Tendências Tech",
            "Dicas Profissionais"
        ]
    
    def get_daily_topic(self) -> str:
        """Returns a topic based on day of week with added randomness for variety."""
        day_of_week = datetime.datetime.now().weekday()
        base_topic = self.topics[day_of_week % len(self.topics)]
        
        # Add a sub-angle to the topic for more variety
        sub_angles = [
            "trends and future",
            "practical tips",
            "personal experience",
            "common mistakes to avoid",
            "key skills needed"
        ]
        return f"{base_topic} ({random.choice(sub_angles)})"

    
    def generate_varied_post(self, resume_context: str) -> Optional[str]:
        """Generates a post with varied content based on daily topic."""
        topic = self.get_daily_topic()
        
        system_prompt = (
            f"You are a professional LinkedIn content creator. "
            f"Write an engaging post about '{topic}' that is relevant to someone in the "
            f"{self.config.profile.area} field. "
            f"The post should be 3-5 sentences, professional yet approachable. "
            f"Include 2-3 relevant hashtags. "
            f"Language: Portuguese (pt-BR)."
        )
        
        user_prompt = (
            f"Today's topic: {topic}\\n"
            f"Candidate Profile: {self.config.profile.role} at {self.config.profile.level} level.\\n"
            f"Resume Highlights: {resume_context[:300]}...\\n\\n"
            f"Generate an insightful post:"
        )
        
        logger.info(f"Generating post for topic: {topic}")
        return self.ai.ask_gpt(system_prompt, user_prompt)
    
    def generate_image_prompt(self, post_content: str) -> str:
        """Generates a DALL-E prompt based on post content."""
        system_prompt = (
            "You are an expert at creating image prompts for DALL-E. "
            "Based on the LinkedIn post content, create a concise prompt for a professional, "
            "modern image that complements the post. "
            "The image should be suitable for LinkedIn (professional, clean, tech-themed). "
            "Return ONLY the prompt, no explanations."
        )
        
        user_prompt = f"Post content: {post_content}\\n\\nImage prompt:"
        
        result = self.ai.ask_gpt(system_prompt, user_prompt)
        return result or "Professional tech workspace, modern, minimalist, blue and white tones"
    
    def generate_comment(self, post_text: str) -> Optional[str]:
        """Generates an intelligent comment for a LinkedIn post."""
        system_prompt = (
            "You are commenting on a LinkedIn post. "
            "Write a thoughtful, professional comment (2-3 sentences) that adds value. "
            "Be genuine, avoid generic phrases like 'Great post!'. "
            "Language: Portuguese (pt-BR)."
        )
        
        user_prompt = f"Post: {post_text[:500]}\\n\\nYour comment:"
        
        return self.ai.ask_gpt(system_prompt, user_prompt)

    def generate_and_save_image(self, post_content: str) -> Optional[str]:
        """Generates an image via DALL-E and saves it locally. Returns the file path."""
        try:
            prompt = self.generate_image_prompt(post_content)
            image_url = self.ai.generate_image(prompt)
            
            if not image_url:
                return None
            
            # Save image locally
            import urllib.request
            import os
            
            save_dir = os.path.join("data", "generated_images")
            os.makedirs(save_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.abspath(os.path.join(save_dir, f"post_image_{timestamp}.png"))
            
            logger.info(f"Downloading image to {file_path}...")
            urllib.request.urlretrieve(image_url, file_path)
            
            return file_path
        except Exception as e:
            logger.error(f"Failed to generate/save image: {e}")
            return None

