import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from src.config import Settings
from src.lighting_control import LightingController

logger = logging.getLogger(__name__)

class RoomController:
    def __init__(self, config: Settings):
        self.config = config
        self.lighting = LightingController()
        self.spotify = None
        
        # Initialize Spotify if credentials exist
        if config.secrets and config.secrets.spotify:
            try:
                client_id = config.secrets.spotify.get("client_id")
                client_secret = config.secrets.spotify.get("client_secret")
                redirect_uri = config.secrets.spotify.get("redirect_uri", "http://localhost:8888/callback")
                
                if client_id and client_secret:
                    self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
                        client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri,
                        scope="user-modify-playback-state,user-read-playback-state"
                    ))
                    logger.info("🎵 Spotify connected successfully.")
            except Exception as e:
                logger.error(f"Failed to connect to Spotify: {e}")

    def set_scene(self, scene_name: str) -> str:
        """Sets the room atmosphere (Lights + Music)."""
        scene_name = scene_name.lower()
        response = []
        
        if scene_name == "focus":
            # 1. Lights: Blue/Cool White
            # Note: LightingController currently has hardcoded methods, we might need to expand it later.
            # For now, let's assume active mode is close to focus.
            res_light = self.lighting.set_active_mode() 
            response.append(f"💡 {res_light}")
            
            # 2. Music: Lofi or Classical
            res_music = self.play_music(search="lofi beats", type="playlist")
            response.append(f"🎵 {res_music}")
            
        elif scene_name == "party":
            # 1. Lights: Colorful? (Need to implement in LightingController)
            res_light = self.lighting.set_active_mode() # Placeholder
            response.append(f"💡 {res_light}")
            
            # 2. Music: Upbeat
            res_music = self.play_music(search="top hits", type="playlist")
            response.append(f"🎵 {res_music}")
            
        elif scene_name == "chill":
            # 1. Lights: Warm/Dim?
            res_light = self.lighting.set_dark_mode() # Maybe dark is chill?
            response.append(f"💡 {res_light}")
            
             # 2. Music: Acoustic
            res_music = self.play_music(search="acoustic chill", type="playlist")
            response.append(f"🎵 {res_music}")
            
        else:
            return "⚠️ Cenas disponíveis: `focus`, `party`, `chill`."
            
        return "\n".join(response)

    def play_music(self, search: str = "", type: str = "track") -> str:
        """Controls Spotify playback."""
        if not self.spotify:
            return "❌ Spotify não configurado. Adicione credenciais no secrets.yaml."
            
        try:
            # Check if active device exists
            devices = self.spotify.devices()
            if not devices['devices']:
                return "⚠️ Nenhum dispositivo Spotify ativo encontrado. Abra o Spotify no PC/Celular."
            
            device_id = devices['devices'][0]['id']
            
            if search:
                # Search and Play
                results = self.spotify.search(q=search, limit=1, type=type)
                items = results[f'{type}s']['items']
                if not items:
                    return f"❌ Nada encontrado para '{search}'."
                
                uri = items[0]['uri']
                self.spotify.start_playback(device_id=device_id, context_uri=uri if type in ['album', 'playlist'] else None, uris=[uri] if type == 'track' else None)
                return f"Tocando: {items[0]['name']}"
            else:
                # Just Resume
                self.spotify.start_playback(device_id=device_id)
                return "▶️ Resumindo música."
                
        except Exception as e:
            logger.error(f"Spotify Error: {e}")
            return f"❌ Erro no Spotify: {e}"

    def pause_music(self) -> str:
        if not self.spotify: return "❌ Spotify offline."
        try:
            self.spotify.pause_playback()
            return "⏸️ Música pausada."
        except:
            return "⚠️ Erro ao pausar."

    def next_track(self) -> str:
        if not self.spotify: return "❌ Spotify offline."
        try:
            self.spotify.next_track()
            return "⏭️ Próxima música."
        except:
            return "⚠️ Erro ao pular."
