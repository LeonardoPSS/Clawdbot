import logging
import random
import time
from datetime import datetime
from src.linkedin_manager import LinkedInManager

logger = logging.getLogger(__name__)

class LinkedInBooster:
    def __init__(self, linkedin_manager: LinkedInManager):
        self.linkedin = linkedin_manager
        self.ai = linkedin_manager.ai
        self.config = linkedin_manager.config

    def run_viral_post_strategy(self) -> str:
        """
        Generates a high-engagement post with an AI image and publishes it.
        """
        logger.info("🚀 Starting Viral Post Strategy...")
        
        # 1. Choose a trending tech topic
        topics = [
            "The Future of AI Agents in Daily Work",
            "Why Python is still King for Automation",
            "Remote Work vs Office: The Productivity Debate",
            "How I built my own AI Assistant (Nexara)",
            "The importance of Continuous Learning in Tech"
        ]
        topic = random.choice(topics)
        
        # 2. Generate Content
        system_prompt = (
            "You are a LinkedIn Top Voice. Write a viral, engaging post about the given topic. "
            "Hook the reader in the first line. Use bullet points. "
            "End with a thought-provoking question to drive comments. "
            "Language: Portuguese (pt-BR). Max 1500 chars."
        )
        post_content = self.ai.ask_gpt(system_prompt, f"Topic: {topic}")
        
        if not post_content:
            return "❌ Failed to generate post content."

        # 3. Generate Visual (Image)
        image_prompt = (
            f"A futuristic, high-tech, 3D render illustration representing '{topic}'. "
            "Neon colors, cyberpunk style, professional quality. No text."
        )
        image_url = self.ai.generate_image(image_prompt)
        
        image_path = None
        if image_url:
            # Download the image to a temp file
            try:
                import requests
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_path = f"data/temp_post_image_{int(time.time())}.png"
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Downloaded AI generated image to {image_path}")
            except Exception as e:
                logger.error(f"Failed to download generated image: {e}")

        # 4. Publish
        success = self.linkedin.create_post(post_content, image_path)
        
        # Cleanup
        if image_path:
            try:
                import os
                os.remove(image_path)
            except: pass

        if success:
            return f"✅ Viral Post Published! Topic: {topic}"
        else:
            return "❌ Failed to publish post on LinkedIn."

    def run_smart_networking_strategy(self) -> str:
        """
        Finds recruiters at top companies and connects with them.
        """
        logger.info("🤝 Starting Smart Networking Strategy...")
        
        target_companies = ["Google", "Amazon", "Microsoft", "Nubank", "Mercado Livre", "Itaú"]
        company = random.choice(target_companies)
        
        recruiters = self.linkedin.search_recruiters(company)
        if not recruiters:
            return f"⚠️ No recruiters found for {company}."
            
        count = 0
        for recruiter in recruiters[:2]: # Limit to 2 per run to be safe
            success = self.linkedin.send_connection_request(recruiter, "Resume context placeholder")
            if success:
                count += 1
                time.sleep(random.randint(5,10))
                
        return f"✅ Connected with {count} recruiters at {company}."

    def perform_profile_audit(self) -> str:
        """Wraps the manager's audit."""
        return self.linkedin.perform_profile_audit()
