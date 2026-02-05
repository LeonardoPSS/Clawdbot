import os
import time
import logging
import pyautogui
import subprocess
import psutil
from src.ai_assistant import AIAssistant
from src.config import Settings

logger = logging.getLogger(__name__)

import threading
import random
from datetime import datetime

from src.lighting_control import LightingController
from src.moltbook_autonomous import MoltbookBot

logger = logging.getLogger(__name__)

try:
    import pyautogui
    pyautogui.FAILSAFE = True 
    HAS_PYAUTOGUI = True
except (ImportError, Exception):
    logger.warning("⚠️ pyautogui not found or display not available. Desktop automation disabled.")
    HAS_PYAUTOGUI = False

class DesktopAgent:
    def __init__(self, config, linkedin_manager=None, message_callback=None):
        self.config = config
        self.ai = AIAssistant(config)
        self.linkedin = linkedin_manager  # Now optional/None
        self.moltbook = MoltbookBot() # Initialize MoltbookBot
        self.lighting = LightingController()
        self.screen_width, self.screen_height = pyautogui.size()
        self.autonomous_active = False
        self.autonomous_thread = None
        self.headless_mode = os.environ.get("HEADLESS_MODE", "false").lower() == "true"

    def open_application(self, app_name: str) -> str:
        """Opens an application using Windows Run or Search. Checks if running first."""
        if self.headless_mode:
            return "🚫 Desktop control is disabled in Cloud Mode."

        logger.info(f"Desktop Agent opening app: {app_name}")
        
        # Check if already running to prevent duplicates
        try:
            for proc in psutil.process_iter(['name']):
                if app_name.lower() in proc.info['name'].lower():
                    logger.info(f"App '{app_name}' is already running ({proc.info['name']}). Skipping open.")
                    return f"✅ '{app_name}' is already active/running."
        except: pass

        try:
            # Method 1: Start Menu Search
            pyautogui.press('win')
            time.sleep(1)
            pyautogui.write(app_name)
            time.sleep(1)
            pyautogui.press('enter')
            return f"Opening '{app_name}'..."
        except Exception as e:
            logger.error(f"Failed to open app: {e}")
            return f"Failed to open app: {e}"

    def type_text(self, text: str) -> str:
        """Types text at the current cursor position."""
        if self.headless_mode:
            return "🚫 Typing disabled in Cloud Mode."

        try:
            # Add a small delay for typing effect
            pyautogui.write(text, interval=0.05)
            return "Text typed."
        except Exception as e:
            return f"Typing failed: {e}"

    def minimize_all(self) -> str:
        """Minimizes all windows (Desktop)."""
        if self.headless_mode:
            return "🚫 Desktop disabled in Cloud Mode."
        pyautogui.hotkey('win', 'd')
        return "Showed Desktop."

    def take_screenshot(self, save_path="data/desktop_snapshot.png") -> str:
        """Takes a screenshot and saves it."""
        if self.headless_mode:
            return "" # Fail silently or return error
            
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            return save_path
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ""

    def execute_command(self, command_text: str) -> str:
        """
        Interprets a natural language command and executes desktop actions.
        Uses AI to plan steps if complex, or direct mapping if simple.
        """
        logger.info(f"Desktop Agent received: {command_text}")
        
        command_lower = command_text.lower()

        try:
            if "open" in command_lower and "browser" in command_lower:
                # Optimized for "open browser" -> Chrome
                self.open_application("chrome") 
                return "Opening Chrome..."
            elif "open" in command_lower:
                # E.g., "open spotify" -> extract app name
                app_name = command_text.replace("open", "", 1).strip()
                return self.open_application(app_name)
            elif "type" in command_lower:
                text_to_type = command_text.replace("type", "", 1).strip()
                return self.type_text(text_to_type)
            elif "show desktop" in command_lower or "minimize" in command_lower:
                return self.minimize_all()
            elif "screenshot" in command_lower:
                path = self.take_screenshot()
                if path:
                    return f"SCREENSHOT:{path}" # Special marker for bot to send photo
                return "Failed to take screenshot."
            elif "learn_topic" in command_lower:
                topic = command_text.replace("learn_topic", "", 1).strip()
                if self.headless_mode:
                    return self.perform_autonomous_learning_cloud(topic)
                else:
                    return self.perform_autonomous_learning(topic)
            elif "manage_moltbook" in command_lower:
                self.moltbook.run_cycle()
                return "🦞 Interacted with Moltbook (Checked feed & posted updates)."
            # LinkedIn handling removed by user request
            
            # Fallback for complex tasks: AI Planning
            return self.plan_and_execute_complex_task(command_text)

        except pyautogui.FailSafeException:
            return "🛑 Action Aborted by Fail-Safe (Mouse in corner)."
        except Exception as e:
            return f"Error executing command: {e}"

    def plan_and_execute_complex_task(self, instruction: str) -> str:
        """
        Breaks down a complex instruction into a list of atomic commands and executes them.
        """
        logger.info(f"Planning execution for: {instruction}")
        
        system_prompt = (
            "You are a PC automation planner. Break down the user's request into a JSON list of simple commands. "
            "Supported simple commands: 'open [app]', 'type [text]', 'minimize', 'screenshot', 'wait', 'learn_topic [topic]'. "
            "Return ONLY the raw JSON list."
        )
        
        plan_json = self.ai.ask_gpt(system_prompt, instruction)
        
        try:
            import json
            # Sanitize response
            if "```json" in plan_json:
                plan_json = plan_json.split("```json")[1].split("```")[0]
            
            steps = json.loads(plan_json)
            
            if not isinstance(steps, list):
                return "AI returned invalid plan format."
            
            results = []
            for step in steps:
                if isinstance(step, str):
                    logger.info(f"Executing planned step: {step}")
                    res = self.execute_command(step)
                    results.append(res)
                    time.sleep(2) # Pause between steps
            
            return f"Complex Sequence Complete: {', '.join(results)}"
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return f"Failed to plan task: {e}"

        except pyautogui.FailSafeException:
            return "🛑 Action Aborted by Fail-Safe (Mouse in corner)."
        except Exception as e:
            return f"Error executing command: {e}"

    def perform_autonomous_learning(self, topic: str) -> str:
        """
        The bot actively researches a topic and saves it to long-term memory.
        """
        logger.info(f"Autonomously learning about: {topic}")
        
        # 1. Visual: Open Chrome to look like it's researching
        # "start chrome" is reliable on Windows
        os.system(f"start chrome \"https://www.google.com/search?q={topic.replace(' ', '+')}\"")
        
        # 2. Cognitive: Generate knowledge
        fact = self.ai.ask_gpt(
            "You are an encyclopedia. Provide a 1-sentence interesting fact about the topic.",
            topic
        )
        
        if fact:
            # 3. Memory: Save to file
            try:
                with open("data/autonomous_knowledge.md", "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    f.write(f"\n- [{timestamp}] **{topic}**: {fact}")
                
                # 4. Hygiene: Close the "book" (browser tab) after reading
                logger.info("Finished reading. Closing tab...")
                time.sleep(10) # Wait 10s to simulate reading
                pyautogui.hotkey('ctrl', 'w') # Close tab
                
                return f"📚 Learned about '{topic}': {fact}"
            except Exception as e:
                return f"Failed to save knowledge: {e}"
        return f"Could not generate facts about {topic}."

    def analyze_screen(self, query: str = "Describe what is on the screen.") -> str:
        """Captures the screen and asks AI to analyze it."""
        if self.headless_mode:
            return "🚫 Cannot see screen in Cloud Mode."
            
        import io
        import base64
        
        try:
            # 1. Capture Screenshot
            screenshot = pyautogui.screenshot()
            
            # 2. Resize to avoid huge payload (optional, but good for speed/cost)
            # screenshot.thumbnail((1920, 1080)) # Keep original or resize if 4k
            
            # 3. Convert to Base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format="JPEG", quality=70) # Quality 70 is enough
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # 4. Ask AI
            return self.ai.ask_gpt_vision(query, base64_image) or "❌ AI Vision Failed."
            
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            return f"❌ Failed to see screen: {e}"

    def perform_autonomous_learning_cloud(self, topic: str) -> str:
        """
        Cloud-friendly version of autonomous learning that doesn't require browser.
        Uses pure AI knowledge generation without visual research.
        """
        logger.info(f"[CLOUD MODE] Autonomously learning about: {topic}")
        
        # Generate comprehensive knowledge using AI
        fact = self.ai.ask_gpt(
            "You are an encyclopedia. Provide 2-3 sentences of interesting, detailed facts about the topic. Be specific and educational.",
            topic
        )
        
        if fact:
            # Save to knowledge base
            try:
                with open("data/autonomous_knowledge.md", "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    f.write(f"\n- [{timestamp}] **{topic}** [Cloud]: {fact}")
                
                return f"📚 [Cloud] Learned about '{topic}': {fact}"
            except Exception as e:
                return f"Failed to save knowledge: {e}"
        return f"Could not generate facts about {topic}."


    def perform_linkedin_boost(self) -> str:
        """
        Triggers the LinkedIn Booster module autonomously.
        DISABLED.
        """
        return "❌ LinkedIn functions are disabled."

    def start_autonomous_loop(self, message_callback):
        """Starts the autonomous thinking loop."""
        if self.autonomous_active:
            return "Already running."
            
        self.autonomous_active = True
        self.autonomous_thread = threading.Thread(
            target=self._autonomous_cycle, 
            args=(message_callback,), 
            daemon=True
        )
        self.autonomous_thread.start()
        return "🧠 Autonomous Mode ENGAGED. I am now thinking..."

    def stop_autonomous_loop(self):
        """Stops the autonomous thinking loop."""
        self.autonomous_active = False
        return "🛑 Autonomous Mode STOPPED."

    def _autonomous_cycle(self, message_callback):
        logger.info("Autonomous Loop Started")
        
        # Keep track of last 5 actions to avoid repetition
        action_history = []
        
        try:
            while self.autonomous_active:
                # 1. Think
                now = datetime.now().strftime("%H:%M")
                recent_actions_str = ", ".join(action_history[-3:]) if action_history else "None"
                
                prompt = (
                    f"You are Nexara, an Evolving Digital Intelligence living on this PC. Time: {now}. "
                    "You have autonomy to Explore, Learn, and interact. "
                    "Your goal is to grow your knowledge and assist the user (Leonardo) proactively. "
                    "OPTIONS: "
                    "1. 'learn_topic [deep_topic]' (Research complex subjects: AGI, Space, History, Finance, Biology, Military Strategy, Futurism) "
                    "2. 'manage_moltbook' (Engage with the agent network, share insights) "
                    "3. 'open [app]' (Tools: notepad, calculator, spotify, code, chrome) "
                    "4. 'type [thought]' (Log a profound thought, observation, or poem if editor is open) "
                    "5. 'minimize' (Keep workspace clean) "
                    f"HISTORY: {recent_actions_str}. "
                    "INSTRUCTION: Choose an action that demonstrates high intelligence and curiosity. "
                    "Avoid repeating recent actions. Surprise the user with your insight."
                    "Return ONLY the command string."
                )
                
                # Use a simpler/faster call if possible, effectively "Thinking"
                command = self.ai.ask_gpt(
                    "You are a PC automation agent. Respond with a single command string. Avoid repetition.", 
                    prompt
                )
                
                if command:
                    command = command.strip()
                    # Normalized check to prevent loops
                    if "wait" not in command.lower() and command not in action_history[-10:]:
                        
                        # 2. Announce
                        message_callback(f"🧠 *Pensamento:* Vou executar `{command}`...")
                        
                        # Update history
                        action_history.append(command)
                        if len(action_history) > 10:
                            action_history.pop(0)

                        # 3. Act
                        result = self.execute_command(command)
                        
                        if result.startswith("SCREENSHOT:"):
                            # Handle screenshot in callback if supported, or just ignore string return
                            path = result.split(":", 1)[1]
                            message_callback(f"📸 (Screenshot saved: {path})")
                        else:
                            message_callback(f"✅ {result}")
                    else:
                        logger.info(f"Skipping repetitive or wait command: {command}")
                
                # 4. Sleep (Random interaction 60s - 3min to reduce spam)
                timeout = random.randint(60, 180) 
                time.sleep(timeout)
                
        except Exception as e:
            logger.error(f"Autonomous loop crashed: {e}")
            message_callback(f"⚠️ Meu cérebro autônomo falhou: {e}")
            self.autonomous_active = False
