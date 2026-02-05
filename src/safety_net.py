import os
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SafetyNet:
    """
    Guardian of Nexara's Codebase.
    Responsible for backing up source code before any self-mutation.
    """
    def __init__(self, backup_dir="backups"):
        self.backup_dir = os.path.join(os.getcwd(), backup_dir)
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_snapshot(self, label: str = "auto") -> str:
        """Creates a zipped backup of the 'src' directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"snapshot_{timestamp}_{label}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        src_path = os.path.join(os.getcwd(), "src")
        
        try:
            shutil.make_archive(backup_path, 'zip', src_path)
            logger.info(f"🛡️ SafetyNet: Backup created at {backup_path}.zip")
            return f"{backup_path}.zip"
        except Exception as e:
            logger.error(f"❌ SafetyNet Failed: {e}")
            return None

    def restore_snapshot(self, backup_path: str):
        """Restores code from a backup (Nuclear Option)."""
        # Logic to unzip and replace src/ would go here.
        # This is dangerous to implement automatically without manual override.
        # For now, we just log where the backup is.
        pass
