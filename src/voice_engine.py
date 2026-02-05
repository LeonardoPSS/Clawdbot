import os
import logging
from gtts import gTTS
from src.ai_assistant import AIAssistant
from src.config import Settings
import tempfile

logger = logging.getLogger(__name__)

class VoiceEngine:
    def __init__(self, config: Settings):
        self.config = config
        self.ai = AIAssistant(config) # Re-use AI for config access, though Whisper usage is direct via client if using new lib, or API otherwise.
        # Ideally, we should use the OpenAI client from ai_assistant if it exposes it, 
        # but AIAssistant uses raw requests. We can add a transcribe method there or here.
        self.output_dir = os.path.join(os.getcwd(), "data", "voice_cache")
        os.makedirs(self.output_dir, exist_ok=True)

    def text_to_speech(self, text: str, lang: str = "pt") -> str:
        """Converts text to MP3 using Google TTS."""
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            filename = f"speech_{hash(text)}.mp3"
            filepath = os.path.join(self.output_dir, filename)
            tts.save(filepath)
            return filepath
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            return None

    def speech_to_text(self, audio_path: str) -> str:
        """Transcribes audio using OpenAI Whisper (via AIAssistant helper)."""
        # We need to implement a transcribe method in AIAssistant or use valid API call here
        return self.ai.transcribe_audio(audio_path)
