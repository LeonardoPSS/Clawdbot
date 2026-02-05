import logging
import json
from fpdf import FPDF
import openai

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class AIStudyPlanner:
    def __init__(self, api_key, topics):
        self.api_key = api_key
        self.topics = topics
        self.schedule = None
        openai.api_key = self.api_key

    def generate_study_schedule(self):
        logging.info("Generating study schedule using GPT-3")
        prompt = self._create_prompt()
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            self.schedule = response.choices[0].text.strip()
            logging.info("Study schedule generated successfully")
        except Exception as e:
            logging.error(f"Error generating study schedule: {e}")
            self.schedule = None

    def _create_prompt(self):
        logging.debug("Creating prompt for GPT-3")
        prompt = "Create an optimized study schedule for the following topics:\n"
        for topic in self.topics:
            prompt += f"- {topic}\n"
        prompt += "The schedule should be efficient and cover all topics thoroughly."
        logging.debug(f"Prompt created: {prompt}")
        return prompt

    def save_schedule_to_pdf(self, filename):
        if not self.schedule:
            logging.error("No schedule to save. Please generate the schedule first.")
            return

        logging.info(f"Saving schedule to PDF: {filename}")
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, self.schedule)
            pdf.output(filename)
            logging.info("Schedule saved to PDF successfully")
        except Exception as e:
            logging.error(f"Error saving schedule to PDF: {e}")

# Example usage
if __name__ == "__main__":
    api_key = "your_openai_api_key"
    topics = ["Machine Learning", "Data Science", "Python Programming", "Statistics"]
    planner = AIStudyPlanner(api_key, topics)
    planner.generate_study_schedule()
    planner.save_schedule_to_pdf("study_schedule.pdf")