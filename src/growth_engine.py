import os
import logging
import glob
from src.ai_assistant import AIAssistant
from src.config import Settings
from src.safety_net import SafetyNet

logger = logging.getLogger(__name__)

class GrowthEngine:
    """
    The Meta-Cognition Module.
    Allows Nexara to audit, plan, and write her own code.
    """
    def __init__(self, config: Settings):
        self.config = config
        self.ai = AIAssistant(config)
        self.safety = SafetyNet()
        self.src_dir = os.path.join(os.getcwd(), "src")

    def _read_codebase(self) -> str:
        """Reads all python files in src/ to form a context."""
        context = ""
        files = glob.glob(os.path.join(self.src_dir, "*.py"))
        for file in files:
            if "growth_engine.py" in file: continue # Avoid reading self to prevent infinite loops? Actually, she should read self too.
            
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                filename = os.path.basename(file)
                context += f"\n--- FILE: {filename} ---\n{content}\n"
        return context

    def audit_self(self) -> str:
        """Analyzes own code for improvements."""
        logger.info("🧠 GrowthEngine: Starting self-audit...")
        code_context = self._read_codebase()
        
        # Limit context if too huge (naive approach)
        if len(code_context) > 100000:
             code_context = code_context[:100000] + "\n... (truncated)"

        prompt = (
            "You are an AGI Architect analyzing your own source code.\n"
            "Identify distinct areas for improvement: Optimization, New Features, or Refactoring.\n"
            "Focus on high-impact changes that increase autonomy or intelligence.\n"
            "Return a bulleted list of potential 'Evolutionary Leaps'."
        )
        
        return self.ai.ask_gpt(prompt, f"MY SOURCE CODE:\n{code_context}")

    def generate_skill(self, instruction: str) -> str:
        """Writes a new Python module based on instruction."""
        logger.info(f"🧬 GrowthEngine: Mutating code - {instruction}...")
        
        # 1. Safety First
        self.safety.create_snapshot(label="pre_evolution")
        
        # 2. Design Code
        prompt = (
            f"Write a Python module (class) that implements: {instruction}.\n"
            "The code must be self-contained, robust, and use existing project patterns (logging, config).\n"
            "Return ONLY the python code inside ```python blocks."
        )
        
        code = self.ai.ask_gpt(prompt, "Create this new skill.")
        
        # Extract code block
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        
        # 3. Save Code (Mutation)
        # Naming is tricky. Let's use specific names or random.
        # AI should suggest filename? taking risk:
        filename = f"skill_{abs(hash(instruction)) % 10000}.py"
        filepath = os.path.join(self.src_dir, "skills", filename)
        os.makedirs(os.path.join(self.src_dir, "skills"), exist_ok=True)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)
            
            # GOD MODE: Auto-Load
            load_result = self.load_skill_dynamically(filepath)
            return f"🧬 SUCCESS: New skill evolved at `src/skills/{filename}`.\n⚡ God Mode: {load_result}"
        except Exception as e:
            return f"❌ Mutation Failed: {e}"

    def load_skill_dynamically(self, filepath: str) -> str:
        """Injects the new code into the running brain."""
        import importlib.util
        import sys
        
        try:
            module_name = os.path.basename(filepath).replace(".py", "")
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Check if it has a register or main function to run?
            # For now, just loading the class/functions is enough to make them 'exist'
            # Ideally, we would have a standardized 'register(bot)' function.
            
            return "Skill Loaded & Active."
        except Exception as e:
            logger.error(f"Failed to load skill: {e}")
            return f"Saved, but failed to load: {e}"
