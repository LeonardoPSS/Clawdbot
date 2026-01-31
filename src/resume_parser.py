import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from pdfminer.high_level import extract_text as extract_pdf_text
import docx

# Configure logger
logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {self.file_path}")
        
        self.raw_text = ""
        self.parsed_data = {
            "email": None,
            "phone": None,
            "skills": [],
            "education": [],
            "experience": []
        }

    def read_file(self) -> str:
        """Reads the file content based on extension."""
        extension = self.file_path.suffix.lower()
        try:
            if extension == '.pdf':
                self.raw_text = extract_pdf_text(self.file_path)
            elif extension == '.docx':
                doc = docx.Document(self.file_path)
                self.raw_text = "\n".join([para.text for para in doc.paragraphs])
            else:
                raise ValueError(f"Unsupported file format: {extension}")
            
            logger.info(f"Successfully read resume: {self.file_path.name}")
            return self.raw_text
        except Exception as e:
            logger.error(f"Error reading resume file: {e}")
            raise

    def extract_contact_info(self):
        """Extracts email and phone number using regex."""
        # Email regex
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', self.raw_text)
        if email_match:
            self.parsed_data["email"] = email_match.group(0)

        # Phone regex (simple generic version, can be improved for BR format)
        # Matches: (XX) XXXXX-XXXX or XX XXXXX-XXXX
        phone_match = re.search(r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}', self.raw_text)
        if phone_match:
            self.parsed_data["phone"] = phone_match.group(0)

    def parse(self) -> Dict:
        """Main parsing method to extract all info."""
        if not self.raw_text:
            self.read_file()
        
        self.extract_contact_info()
        # Future: Add specific skill/experience extraction logic here
        # For now, we return the raw text + contacts to be used by the bot
        
        return {
            "raw_text": self.raw_text,
            "extracted": self.parsed_data
        }

if __name__ == "__main__":
    # Test with dummy file logic if needed
    pass
