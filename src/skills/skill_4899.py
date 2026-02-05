import logging
import json
import os
from fpdf import FPDF
import openai

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class AIStudyPlanner:
    def __init__(self, api_key: str, config_file: str = 'config.json'):
        self.api_key = api_key
        self.config = self.load_config(config_file)
        openai.api_key = self.api_key

    def load_config(self, config_file: str):
        if not os.path.exists(config_file):
            logging.error(f"Config file {config_file} not found.")
            return {}
        with open(config_file, 'r') as file:
            config = json.load(file)
        logging.debug(f"Config loaded: {config}")
        return config

    def generate_study_plan(self, topics: list):
        prompt = self.create_prompt(topics)
        logging.debug(f"Generated prompt for GPT: {prompt}")
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1500
        )
        study_plan = response.choices[0].text.strip()
        logging.info("Study plan generated successfully.")
        return study_plan

    def create_prompt(self, topics: list):
        topics_str = ', '.join(topics)
        prompt = (
            f"Create an optimized study schedule for the following topics: {topics_str}. "
            "The schedule should be efficient, balanced, and suitable for a student preparing for exams."
        )
        return prompt

    def save_to_pdf(self, study_plan: str, filename: str = 'study_plan.pdf'):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, study_plan)
        pdf.output(filename)
        logging.info(f"Study plan saved to {filename}")

# Example usage:
# planner = AIStudyPlanner(api_key='your_openai_api_key')
# topics = ['Machine Learning', 'Data Structures', 'Algorithms', 'Statistics']
# study_plan = planner.generate_study_plan(topics)
# planner.save_to_pdf(study_plan)