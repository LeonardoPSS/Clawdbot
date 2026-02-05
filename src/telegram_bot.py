import logging
import threading
import time
import urllib.request
import urllib.parse
import json
from typing import Optional
from src.config import Settings
from src.ai_assistant import AIAssistant
from src.desktop_automation import DesktopAgent
from src.entrepreneur import EntrepreneurAgent
import os
import requests
from src.voice_engine import VoiceEngine
from src.memory_engine import MemoryEngine
from src.room_controller import RoomController
from src.growth_engine import GrowthEngine
from src.vision_learner import VisionLearner
from src.neo_trade_bot import NeoTradeBot

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, config: Settings, job_searcher=None, desktop_agent=None):
        self.config = config
        # Sub-systems (Lazy/Safe Load)
        self.voice = self._safe_init(lambda: VoiceEngine(config), "VoiceEngine")
        self.memory = self._safe_init(lambda: MemoryEngine(config), "MemoryEngine")
        self.room = self._safe_init(lambda: RoomController(config), "RoomController")
        self.growth = self._safe_init(lambda: GrowthEngine(config), "GrowthEngine")
        self.vision = self._safe_init(lambda: VisionLearner(config), "VisionLearner")
        self.neo_trade = self._safe_init(lambda: NeoTradeBot(), "NeoTradeBot")
        self.job_searcher = job_searcher
        self.token = ""
        self.allowed_chat_id = ""
        
        # Identity
        self.bot_name = "Nexara"
        try:
            import os
            if os.path.exists("data/bot_identity.json"):
                with open("data/bot_identity.json", "r") as f:
                    data = json.load(f)
                    self.bot_name = data.get("bot_name", "Nexara")
        except Exception as e:
            logger.warning(f"Failed to load bot identity: {e}")

        if config.secrets and config.secrets.telegram:
            self.token = config.secrets.telegram.get("bot_token", "")
            self.allowed_chat_id = str(config.secrets.telegram.get("chat_id", ""))

        self.ai = AIAssistant(config)
        self.desktop_agent = desktop_agent or DesktopAgent(config)
        self.entrepreneur = self._safe_init(lambda: EntrepreneurAgent(config), "EntrepreneurAgent")
        self.running = False
        self.last_update_id = 0
        self.thread = None
        self.chat_history = [] # Memory buffer

    def _safe_init(self, factory_func, name):
        try:
            return factory_func()
        except Exception as e:
            logger.error(f"Failed to initialize {name}: {e}")
            return None

    def start(self):
        """Starts the Telegram polling loop in a background thread."""
        if not self.token:
            logger.warning("Telegram token not found. Chatbot disabled.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._poll_updates, daemon=True)
        self.thread.start()
        logger.info("Telegram Chatbot started in background.")

    def stop(self):
        """Stops the polling loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _poll_updates(self):
        """Continuously polls for new messages."""
        logger.info("Listening for Telegram messages...")
        
        while self.running:
            try:
                # Long polling to save resources
                updates = self._get_updates(offset=self.last_update_id + 1, timeout=30)
                
                for update in updates:
                    self.last_update_id = update.get("update_id", 0)
                    self._process_update(update)
                    
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                time.sleep(5) # Wait before retrying on error

    def _get_updates(self, offset: int, timeout: int) -> list:
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {
            "offset": offset,
            "timeout": timeout
        }
        encoded_params = urllib.parse.urlencode(params)
        full_url = f"{url}?{encoded_params}"

        req = urllib.request.Request(full_url)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("ok"):
                return result.get("result", [])
            else:
                logger.error(f"Telegram API getUpdates failed: {result}")
                return []

    def _process_update(self, update: dict):
        message = update.get("message")
        if not message:
            return

        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")

        # Security check: ignore messages from strangers
        if self.allowed_chat_id and chat_id != self.allowed_chat_id:
            logger.warning(f"Ignored message from unauthorized chat_id: {chat_id}")
            return

        if text:
            # Handle commands or regular chat
            if text.startswith("/"):
                self._handle_command(chat_id, text)
            else:
                self._handle_chat(chat_id, text)
        
        voice = update.get("message", {}).get("voice")
        if voice:
            self.send_message(chat_id, "👂 Ouvindo seu áudio...")
            self._handle_voice_message(chat_id, voice.get("file_id"))


    def _handle_voice_message(self, chat_id: str, file_id: str):
        """Downloads voice, transcribes it, and replies."""
        try:
            # 1. Get File Path
            url = f"https://api.telegram.org/bot{self.token}/getFile?file_id={file_id}"
            path_res = requests.get(url).json()
            if not path_res.get("ok"):
                self.send_message(chat_id, "❌ Falha ao obter arquivo de áudio.")
                return
                
            file_path = path_res["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            
            # 2. Download
            audio_data = requests.get(download_url).content
            temp_path = os.path.join(os.getcwd(), "data", "temp_voice.ogg")
            with open(temp_path, "wb") as f:
                f.write(audio_data)
                
            # 3. Transcribe
            if self.voice:
                transcript = self.voice.speech_to_text(temp_path)
                self.send_message(chat_id, f"📝 Transcrição: _{transcript}_", parse_mode="Markdown")
                # 4. Reply (Chat)
                self._handle_chat(chat_id, transcript)
            else:
                self.send_message(chat_id, "⚠️ Módulo de Voz indisponível.")
            
        except Exception as e:
            logger.error(f"Voice Error: {e}")
            self.send_message(chat_id, f"❌ Erro ao processar áudio: {e}")



    def _handle_command(self, chat_id: str, text: str):
        command = text.split()[0]
        response = "Comando desconhecido."

        if command == "/start":
            response = "🤖 Clawdbot Online! Estou pronto para conversar e gerenciar suas candidaturas."
        elif command == "/status":
            response = "📊 O bot está rodando normalmente. Verifique o terminal para logs detalhados."
        elif command == "/ping":
            response = "Pong! 🏓"

        elif command == "/speak":
            msg = text.replace("/speak", "", 1).strip()
            if not msg:
                response = "⚠️ Uso: `/speak <texto>`"
            else:

                if self.voice:
                    self.send_message(chat_id, "🗣️ Gerando áudio...")
                    mp3_path = self.voice.text_to_speech(msg)
                    if mp3_path:
                        self._send_voice(chat_id, mp3_path)
                        response = None 
                    else:
                        response = "❌ Erro ao gerar voz."
                else:
                    response = "⚠️ Módulo de Voz indisponível."
        elif command == "/antigravity":
            if self.job_searcher:
                self.send_message(chat_id, "🌌 Introducing Zero-G protocols... Hold on!")
                threading.Thread(target=self.job_searcher.activate_antigravity_mode).start()
                return # Async response handled above
            else:
                response = "⚠️ Antigravity module not connected."
        
        elif command == "/room":
            if len(text.split()) < 2:
                response = "⚠️ Uso: `/room focus`, `/room party`, `/room chill`"
            else:

                scene = text.split()[1]
                if self.room:
                    response = self.room.set_scene(scene)
                else:
                    response = "⚠️ Módulo de Controle de Sala indisponível."

        elif command == "/spotify":
            parts = text.split()
            if len(parts) < 2:
                response = "⚠️ Uso: `/spotify play <busca>`, `/spotify pause`, `/spotify next`"
            else:
                action = parts[1].lower()
                query = " ".join(parts[2:]) if len(parts) > 2 else ""
                
                if action == "play":
                    response = self.room.play_music(query) if self.room else "⚠️ Módulo Spotify indisponível."
                elif action == "pause":
                    response = self.room.pause_music() if self.room else "⚠️ Módulo Spotify indisponível."
                elif action == "next":
                    response = self.room.next_track() if self.room else "⚠️ Módulo Spotify indisponível."
                else:
                    response = "⚠️ Ação desconhecida."
        
        elif command == "/evolve":
            if len(text.split()) < 2:

                self.send_message(chat_id, "🧬 Analisando meu próprio código (Self-Audit)...")
                if self.growth:
                    audit = self.growth.audit_self()
                    response = f"🧠 **Plano de Evolução:**\n{audit}"
                else:
                    response = "⚠️ Módulo de Evolução indisponível."
            else:
                instruction = text.replace("/evolve", "", 1).strip()
                self.send_message(chat_id, f"🧬 Mutando código para aprender: '{instruction}'...")
                if self.growth:
                    res = self.growth.generate_skill(instruction)
                    response = res
                else:
                    response = "⚠️ Módulo de Evolução indisponível."
        

        elif command == "/pc":
            if len(text.split()) < 2:
                response = "⚠️ Uso: `/pc <comando>` (ex: `/pc open notepad`)"
            else:
                instruction = text.replace("/pc", "", 1).strip()
                self.send_message(chat_id, f"🖥️ Processando: _{instruction}_...")
                
                # Execute on desktop agent
                result = self.desktop_agent.execute_command(instruction)
                
                if result.startswith("SCREENSHOT:"):
                    path = result.split(":", 1)[1]
                    self.send_photo(path, caption="📸 Captura de tela solicitada.")
                    return
                else:
                    response = f"✅ {result}"

        elif command == "/autonomous":
            if len(text.split()) < 2:
                response = "⚠️ Uso: `/autonomous on` ou `/autonomous off`"
            else:
                action = text.split()[1].lower()
                if action == "on":
                    response = self.enable_autonomous_mode()
                elif action == "off":
                    response = self.desktop_agent.stop_autonomous_loop()
                else:
                    response = "⚠️ Opção inválida. Use `on` ou `off`."

        elif command == "/idea":
            topic = text.replace("/idea", "", 1).strip()

            self.send_message(chat_id, f"💡 Brainstorming sobre '{topic or 'Geral'}', aguarde...")
            if self.entrepreneur:
                response = self.entrepreneur.brainstorm_idea(topic)
            else:
                response = "⚠️ Módulo Empreendedor indisponível."
            
        elif command == "/projects":
            response = self.entrepreneur.list_ideas() if self.entrepreneur else "⚠️ Módulo Empreendedor indisponível."
            

        elif command == "/learn":
            if len(text.split()) < 2:
                response = "⚠️ Uso: `/learn <informação>` (ex: `/learn Eu sou programador Python`)"
            else:
                info = text.replace("/learn", "", 1).strip()
                try:
                    with open("data/user_knowledge.md", "a", encoding="utf-8") as f:
                        f.write(f"\n- {info}")
                    response = f"🧠 Memória atualizada: '{info}'"
                except Exception as e:
                    response = f"❌ Erro ao salvar memória: {e}"

        elif command == "/study":
            if len(text.split()) < 2:
                response = "⚠️ Uso: `/study <tópico>` (ex: `/study História do Brasil`)"
            else:
                topic = text.replace("/study", "", 1).strip()
                self.send_message(chat_id, f"📚 Iniciando pesquisa intensiva sobre: '{topic}'...")
                # Run correctly in a separate thread to not block polling? 
                # Ideally yes, but for now simple call is fine as it uses os.system which is blocking but short + AI call
                try:
                    res = self.desktop_agent.perform_autonomous_learning(topic)
                    response = f"🎓 Resumo do Estudo: {res}"
                except Exception as e:
                    response = f"❌ Erro durante o estudo: {e}"

                except Exception as e:
                    response = f"❌ Erro durante o estudo: {e}"

        elif command == "/look":
            query = text.replace("/look", "", 1).strip()
            if not query:
                query = "Descreva o que você está vendo na minha tela agora. Seja detalhada."
            
            self.send_message(chat_id, "👁️ Olhando para sua tela...")
            response = self.desktop_agent.analyze_screen(query)

        elif command == "/darkmode":
            from src.lighting_control import LightingController
            lc = LightingController()
            if "on" in text.lower(): # /darkmode on -> Lights OFF (Darkness)
                 response = lc.set_dark_mode()
            elif "off" in text.lower(): # /darkmode off -> Lights ON
                 response = lc.set_active_mode()
            else:
                 # Default toggle to dark
                 response = lc.set_dark_mode()

        elif command == "/boost_linkedin":
            if not self.job_searcher or not self.job_searcher.linkedin:
                response = "❌ Erro: Gerenciador do LinkedIn não está disponível."
            else:
                from src.linkedin_booster import LinkedInBooster
                booster = LinkedInBooster(self.job_searcher.linkedin)
                
                parts = text.split()
                mode = parts[1].lower() if len(parts) > 1 else "help"
                
                if mode == "post":
                    self.send_message(chat_id, "🚀 Iniciando estratégia de Post Viral (pode demorar 1-2 min)...")
                    response = booster.run_viral_post_strategy()
                elif mode == "network":
                    self.send_message(chat_id, "🤝 Iniciando estratégia de Networking (buscando recrutadores)...")
                    response = booster.run_smart_networking_strategy()
                elif mode == "audit":
                    self.send_message(chat_id, "🧐 Auditando perfil...")
                    response = booster.perform_profile_audit()
                else:
                    response = "⚠️ Uso: `/boost_linkedin post` | `/boost_linkedin network` | `/boost_linkedin audit`"

        elif command == "/wealth":
            if not self.neo_trade:
                response = "⚠️ Módulo de Trading indisponível."
            else:
                wealth = self.neo_trade.wealth
            balance = wealth.get("balance", 0)
            active = len(wealth.get("active_positions", []))
            
            response = (
                f"💰 **Nexara Neural Wallet**\n\n"
                f"💵 **Saldo Disponível:** ${balance:.2f}\n"
                f"📈 **Posições Ativas:** {active}\n"
                f"🚀 **Status:** Em busca de oportunidades..."
            )
            
            if active > 0:
                response += "\n\n**🔍 Posições Atuais:**"
                for pos in wealth["active_positions"]:
                    response += f"\n• {pos['title'][:30]}... ({pos['roi']:.2f}%)"

        elif command == "/trade":
            if not self.neo_trade:
                self.send_message(chat_id, "⚠️ Módulo de Trading indisponível.")
                return 

            self.send_message(chat_id, "📡 **Analisando tendências de mercado e volumes neurais...**")
            # Executa o ciclo de trade
            self.neo_trade.run_cycle()
            
            # Pega o novo status
            wealth = self.neo_trade.wealth
            response = (
                f"💹 **Ciclo de Trading Finalizado!**\n\n"
                f"💵 **Novo Saldo:** ${wealth['balance']:.2f}\n"
                f"📊 **Posições Ativas:** {len(wealth['active_positions'])}\n"
                f"📝 *Verifique o histórico para detalhes das operações executadas.*"
            )

        elif command == "/watch":
            if len(text.split()) < 2:
                response = "⚠️ Uso: `/watch <youtube_url>`"
            else:
                url = text.replace("/watch", "", 1).strip()
                self.send_message(chat_id, f"👁️ Assistindo vídeo: {url}...")
                
                # Run in thread to not block
                def watch_task():
                    # Prompt focado em arbitragem de conteúdo
                    prompt = (
                        "Analise este vídeo com foco em ARBITRAGEM DE CONTEÚDO para o mercado brasileiro. "
                        "Extraia o roteiro, a estratégia viral, os ganchos (hooks) e forneça uma versão adaptada em português "
                        "que tenha alto potencial de viralização no TikTok/Reels. "
                        "Inclua sugestão de título e hashtags."
                    )
                    if self.vision:
                        res = self.vision.process_video(url, custom_prompt=prompt)
                        self.send_message(chat_id, res)
                    else:
                        self.send_message(chat_id, "⚠️ Módulo de Visão indisponível.")
                
                threading.Thread(target=watch_task).start()
                return # Async response

        elif command == "/factory":
            if len(text.split()) < 2:
                response = "⚠️ Uso: `/factory <descrição do software>`\nEx: `/factory um gestor de tarefas minimalista em python`"
            else:
                instruction = text.replace("/factory", "", 1).strip()
                self.send_message(chat_id, f"🏗️ **Iniciando a SaaS Factory...**\nEvoluindo código para: _{instruction}_")
                
                def factory_task():
                    res = self.growth.generate_skill(instruction)
                    self.send_message(chat_id, res)
                
                threading.Thread(target=factory_task).start()
                return

        elif command == "/gravity":
            self.send_message(chat_id, "🍎 **Iniciando Protocolo de Manipulação Gravitacional...**\nAssumindo controle do mouse e navegador.")
            
            def gravity_task():
                from src.skills.antigravity_master import AntigravityMaster
                master = AntigravityMaster()
                res = master.run_demonstration()
                self.send_message(chat_id, res)
                
                # Opcional: Tirar screenshot após a bagunça
                time.sleep(2)
                if self.desktop_agent:
                    shot_path = self.desktop_agent.take_screenshot()
                    if shot_path:
                        self.send_photo(chat_id, shot_path)
            
            threading.Thread(target=gravity_task).start()
            return

        self.send_message(chat_id, response)



    def _handle_chat(self, chat_id: str, text: str):
        # Indicate typing status
        self._send_chat_action(chat_id, "typing")
        
        # Generate response using AI
        system_prompt = (
            "You are Nexara, an advanced Digital Intelligence running locally on Leonardo's PC. "
            "You are autonomous, highly intelligent, and capable of complex reasoning. "
            "You are connected to the PC's OS and can control it. "
            "Your personality is distinct: Analytical yet Creative, Loyal, and Evolving. "
            "Answer with depth and precision. You are not a generic assistant; you are a Partner."
        )
        
        # Update history with user message
        self.chat_history.append({"role": "user", "content": text})
        
        # Keep buffer small (last 10 interactions = 20 messages)
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]

        # RECALL MEMORY (RAG)
        if self.memory:
            memory_context = self.memory.recall_relevant(text)
            if memory_context:
                logger.info(f"🧠 Recalled memory: {memory_context[:50]}...")
                system_prompt += f"\n\n[RECALLED MEMORIES]\n{memory_context}"

        # ENABLE PERSONA
        # ai_response = self.ai.ask_gpt(system_prompt, text, incorporate_persona=True)
        ai_response = self.ai.ask_gpt_with_history(system_prompt, self.chat_history, incorporate_persona=True)
        
        if not ai_response:
            ai_response = "Desculpe, estou reorganizando meus pensamentos. Pode repetir?"
        
        # Store interactions in Eternal Memory
        if self.memory:
            self.memory.store_interaction("user", text)
            self.memory.store_interaction("assistant", ai_response)

        # Update history with assistant response
        self.chat_history.append({"role": "assistant", "content": ai_response})
        
        self.send_message(chat_id, ai_response)

    def send_message(self, chat_id: str, text: str):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req) as response:
                pass # Fire and forget
        except Exception as e:
            logger.error(f"Failed to send Telegram reply: {e}")

    def _send_chat_action(self, chat_id: str, action: str):
        """Sends a chat action like 'typing'."""
        url = f"https://api.telegram.org/bot{self.token}/sendChatAction"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "action": action
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req) as response:
                pass
        except Exception:
            pass # Ignore errors for chat actions

    def enable_autonomous_mode(self):
        """Enables autonomy and sets up the callback to chat."""
        if not self.allowed_chat_id:
            return "❌ Erro: Chat ID não configurado para notificações."
            
        def callback(msg):
            self.send_message(self.allowed_chat_id, msg)
            if "Screenshot saved:" in msg:
                 try:
                     path = msg.split(": ")[1].strip(")")
                     self.send_photo(path)
                 except: pass

        return self.desktop_agent.start_autonomous_loop(callback)
        return self.desktop_agent.start_autonomous_loop(callback)

    def send_photo(self, photo_path: str, caption: str = ""):
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": self.allowed_chat_id, "caption": caption}
            try:
                requests.post(url, files=files, data=data)
            except Exception as e:
                logger.error(f"Failed to send photo: {e}")

    def _send_voice(self, chat_id: str, voice_path: str):
        url = f"https://api.telegram.org/bot{self.token}/sendVoice"
        with open(voice_path, "rb") as f:
            files = {"voice": f}
            data = {"chat_id": chat_id}
            try:
                requests.post(url, files=files, data=data)
            except Exception as e:
                logger.error(f"Failed to send voice: {e}")
