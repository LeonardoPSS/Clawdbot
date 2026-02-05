import os
import json
import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__, template_folder='.')
CORS(app)

# Caminhos dos dados
DATA_DIR = os.path.join(os.getcwd(), 'data')
WEALTH_PATH = os.path.join(DATA_DIR, 'neural_wealth.json')
SKILLS_DIR = os.path.join(os.getcwd(), 'src', 'skills')

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@app.route('/api/status')
def get_status():
    wealth = load_json(WEALTH_PATH)
    
    # List skills generated
    skills = []
    if os.path.exists(SKILLS_DIR):
        for f in os.listdir(SKILLS_DIR):
            if f.endswith('.py') and f.startswith('skill_'):
                skills.append({
                    "name": f,
                    "date": os.path.getmtime(os.path.join(SKILLS_DIR, f))
                })
    
    return jsonify({
        "wealth": wealth,
        "factory_count": len(skills),
        "skills": sorted(skills, key=lambda x: x['date'], reverse=True)[:5]
    })

@app.route('/')
def main_page():
    return render_template('dashboard.html')

if __name__ == "__main__":
    print("🚀 Nexara Dashboard Server subindo em http://localhost:5005")
    app.run(port=5005, debug=True)
