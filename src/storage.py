import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class Storage:
    def __init__(self, file_path: str = "data/applied_jobs.csv"):
        self.file_path = Path(file_path)
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """Creates the CSV file with headers if it doesn't exist."""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["date", "platform", "title", "company", "location", "link", "status"])
            logger.info(f"Created new storage file at {self.file_path}")

    def is_already_applied(self, link: str) -> bool:
        """Checks if a job link exists in the database."""
        try:
            with open(self.file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["link"] == link:
                        return True
            return False
        except Exception as e:
            logger.error(f"Error reading storage: {e}")
            return False

    def add_application(self, job_data: Dict, status: str = "APPLIED"):
        """Adds a new application record."""
        try:
            with open(self.file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    job_data.get("platform", "Unknown"),
                    job_data.get("title", "Unknown"),
                    job_data.get("company", "Unknown"),
                    job_data.get("location", "Unknown"),
                    job_data.get("link", ""),
                    status
                ])
            logger.info(f"Recorded application for {job_data.get('title')}")
        except Exception as e:
            logger.error(f"Error writing to storage: {e}")

    def get_today_count(self) -> int:
        """Returns the number of applications recorded today."""
        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        try:
            with open(self.file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["date"].startswith(today) and "APPLIED" in row["status"]:
                        count += 1
            return count
        except Exception as e:
            logger.error(f"Error counting today's applications: {e}")
            return 0


if __name__ == "__main__":
    # Test
    db = Storage("data/test_db.csv")
    dummy_job = {"title": "Test Job", "link": "http://example.com/job1"}
    if not db.is_already_applied(dummy_job["link"]):
        db.add_application(dummy_job)
        print("Added job.")
    else:
        print("Job already exists.")
