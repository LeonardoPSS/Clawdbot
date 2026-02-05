import logging
import os
import time
import glob
import json
import yt_dlp
import cv2
import openai
from src.config import Settings
from src.ai_assistant import AIAssistant

logger = logging.getLogger(__name__)

class VisionLearner:
    """
    The 'Eye' of Nexara.
    Downloads videos, extracts frames, and uses GPT-4o Vision to understand them.
    """
    def __init__(self, config: Settings):
        self.config = config
        self.ai = AIAssistant(config)
        self.data_dir = os.path.join(os.getcwd(), "data", "vision_cache")
        os.makedirs(self.data_dir, exist_ok=True)

    def process_video(self, url: str, custom_prompt: str = None) -> str:
        """Full pipeline: Download -> Extract -> Analyze -> Report."""
        logger.info(f"👁️ VisionLearner: Processing {url}...")
        
        try:
            # 1. Download
            video_path = self._download_video(url)
            if not video_path: return "❌ Falha no download do vídeo."

            # 2. Extract Key Frames
            frames = self._extract_frames(video_path, start_min=0, max_frames=5)
            
            # 3. Analyze with GPT-4o Vision
            prompt = custom_prompt or "O que está sendo ensinado neste vídeo? Descreva os passos técnicos."
            analysis = self._analyze_frames(frames, prompt)
            
            # 4. Cleanup
            self._cleanup(video_path, frames)
            
            return f"📺 **Resultado da Análise Visual:**\n\n{analysis}"

        except Exception as e:
            logger.error(f"Vision Error: {e}")
            return f"❌ Erro na visão computacional: {e}"

    def _download_video(self, url: str) -> str:
        """Downloads video using yt-dlp (worst quality to save bandwidth)."""
        ydl_opts = {
            'format': 'worst', # We check code/slides, 360p is enough
            'outtmpl': os.path.join(self.data_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return None

    def _extract_frames(self, video_path: str, start_min: int = 0, max_frames: int = 5) -> list:
        """Extracts N frames distributed across the video."""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps
        
        # Strategy: Get frame at 10%, 30%, 50%, 70%, 90%
        timestamps = [duration * 0.1, duration * 0.3, duration * 0.5, duration * 0.7, duration * 0.9]
        
        count = 0
        for t in timestamps:
            if count >= max_frames: break
            
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if ret:
                frame_path = os.path.join(self.data_dir, f"frame_{count}.jpg")
                cv2.imwrite(frame_path, frame)
                frames.append(frame_path)
                count += 1
                
        cap.release()
        return frames

    def _analyze_frames(self, frame_paths: list, prompt: str) -> str:
        """Sends images to GPT-4o Vision."""
        if not frame_paths: return "Nenhum frame extraído."
        
        # Prepare inputs (simplified for now, ideally base64 encoded)
        # Note: AIAssistant needs an update to handle images list
        # We will do a direct call here or update AIAssistant later.
        # Direct call for now to keep it self-contained in this module
        
        import base64
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        
        for p in frame_paths:
            with open(p, "rb") as img_file:
                b64 = base64.b64encode(img_file.read()).decode('utf-8')
                messages[0]["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

        try:
             client = openai.OpenAI(api_key=self.config.secrets.openai.get("api_key"))
             response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500
            )
             return response.choices[0].message.content
        except Exception as e:
            return f"Erro na IA Visual: {e}"

    def _cleanup(self, video_path: str, frames: list):
        try:
            if os.path.exists(video_path): os.remove(video_path)
            for f in frames:
                if os.path.exists(f): os.remove(f)
        except: pass
