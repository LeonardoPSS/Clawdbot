import os
import subprocess
import logging

logger = logging.getLogger(__name__)

class LightingController:
    def __init__(self):
        self.executable = self._find_openrgb()

    def _find_openrgb(self):
        paths = [
            r"C:\Program Files\OpenRGB\OpenRGB.exe",
            r"C:\Program Files (x86)\OpenRGB\OpenRGB.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\OpenRGB\OpenRGB.exe")
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    def set_dark_mode(self):
        """Turns all lights OFF (Black)."""
        if not self.executable:
            return "❌ OpenRGB not found. Is it installed?"
        
        try:
            # -c 000000 sets color to black
            # -m static sets mode to static
            subprocess.run([self.executable, "--mode", "static", "--color", "000000"], check=True)
            return "🌑 Lights out (Dark Mode activated)."
        except Exception as e:
            logger.error(f"OpenRGB error: {e}")
            return f"❌ Error setting lights: {e}"

    def set_active_mode(self):
        """Turns lights ON (White/Default)."""
        if not self.executable:
            return "❌ OpenRGB not found."
        
        try:
            # Set to White for "Active"
            subprocess.run([self.executable, "--mode", "static", "--color", "FFFFFF"], check=True)
            return "💡 Lights ON (Active Mode)."
        except Exception as e:
            return f"❌ Error setting lights: {e}"
