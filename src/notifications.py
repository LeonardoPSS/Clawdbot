import logging
import urllib.request
import urllib.parse
import json
import os
import mimetypes
import uuid
from src.config import Settings

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, config: Settings):
        self.config = config
        self.enabled = config.notifications.telegram.enabled
        self.token = ""
        self.chat_id = ""
        
        if config.secrets and config.secrets.telegram:
            self.token = config.secrets.telegram.get("bot_token", "")
            self.chat_id = config.secrets.telegram.get("chat_id", "")

    def send_message(self, text: str):
        """Sends a message to the configured Telegram chat."""
        if not self.enabled or not self.token or not self.chat_id:
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                if not result.get("ok"):
                    logger.error(f"Telegram API error: {result.get('description')}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    def send_photo(self, photo_path: str, caption: str = ""):
        """Sends a photo to the configured Telegram chat."""
        if not self.enabled or not self.token or not self.chat_id:
            return

        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        boundary = f"----TelegramBotBoundary{uuid.uuid4().hex}"
        
        parts = []
        # Chat ID part
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{self.chat_id}\r\n'.encode('utf-8'))
        # Caption part
        if caption:
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode('utf-8'))
        # Photo part
        with open(photo_path, 'rb') as f:
            filename = os.path.basename(photo_path)
            mime_type = mimetypes.guess_type(photo_path)[0] or 'application/octet-stream'
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="{filename}"\r\nContent-Type: {mime_type}\r\n\r\n'.encode('utf-8'))
            parts.append(f.read())
            parts.append(b'\r\n')
        
        parts.append(f'--{boundary}--\r\n'.encode('utf-8'))
        body = b''.join(parts)

        try:
            req = urllib.request.Request(url, data=body)
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                if not result.get("ok"):
                    logger.error(f"Telegram API error (photo): {result.get('description')}")
        except Exception as e:
            logger.error(f"Failed to send Telegram photo: {e}")

    def notify_captcha(self, screenshot_path: str, platform: str):
        """Alerts the user when a CAPTCHA is detected."""
        message = (
            f"🧩 *CAPTCHA DETECTADO no {platform}!*\n\n"
            "O bot foi bloqueado por uma verificação de segurança. Por favor, abra o navegador e resolva o desafio para que eu possa continuar!"
        )
        self.send_photo(screenshot_path, caption=message)

    def notify_application(self, job_data: dict, status: str):
        """Specifically formatted notification for a job application."""
        emoji = "✅" if "APPLIED" in status else "⚠️"
        message = (
            f"{emoji} *Nova Inscrição {job_data.get('platform', 'Bot')}*\n\n"
            f"📍 *Vaga:* {job_data.get('title')}\n"
            f"🏢 *Empresa:* {job_data.get('company')}\n"
            f"🗺️ *Local:* {job_data.get('location')}\n"
            f"📊 *Status:* {status}\n\n"
            f"🔗 [Ver Vaga]({job_data.get('link')})"
        )
        self.send_message(message)
    def notify_manual_review(self, job_data: dict):
        """Notification for jobs that require manual application."""
        message = (
            f"📝 *Inscrição Manual Necessária*\n\n"
            f"📍 *Vaga:* {job_data.get('title')}\n"
            f"🏢 *Empresa:* {job_data.get('company')}\n"
            f"🗺️ *Local:* {job_data.get('location')}\n\n"
            f"⚠️ Esta vaga não permite 'Inscrição Simplificada'. Você precisa se inscrever manualmente pelo link abaixo:\n\n"
            f"🔗 [Abrir Link Externo]({job_data.get('link')})"
        )
        self.send_message(message)

    def notify_moltbook_news(self, summary: str):
        """Notification for Moltbook news summaries."""
        message = (
            f"🦞 *Clawdbot Moltbook Update*\n\n"
            f"{summary}\n\n"
            f"🔍 Explore mais em: [moltbook.com](https://www.moltbook.com)"
        )
        self.send_message(message)
