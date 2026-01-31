import yaml
import logging
from pathlib import Path
from typing import List, Optional, Dict, Literal, Union
from pydantic import BaseModel, Field, ValidationError

# Logging setup (temporary until full logging module is ready)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotConfig(BaseModel):
    name: str = "AntigravityJobBot"
    mode: Literal["automatic", "semi-automatic"] = "semi-automatic"
    daily_application_limit: int = Field(default=10, ge=1)
    headless: bool = False

class ProfileKeywords(BaseModel):
    include: List[str] = Field(default_factory=list)
    exclude: List[str] = Field(default_factory=list)

class ProfileConfig(BaseModel):
    role: str
    level: str
    area: str
    locations: List[str]
    keywords: ProfileKeywords

class ResumeConfig(BaseModel):
    file_path: str
    language: str = "pt-BR"
    auto_fill: bool = True

class PlatformSettings(BaseModel):
    enabled: bool = False
    auto_apply: bool = False

class PlatformsConfig(BaseModel):
    linkedin: PlatformSettings = Field(default_factory=PlatformSettings)
    gupy: PlatformSettings = Field(default_factory=PlatformSettings)
    vagas_com: PlatformSettings = Field(default_factory=PlatformSettings)

class DelayRange(BaseModel):
    min: int
    max: int

class EvolutionSettings(BaseModel):
    enabled: bool = False
    daily_post_limit: int = 1
    daily_connection_limit: int = 5
    engagement_keywords: List[str] = Field(default_factory=list)

class BehaviorConfig(BaseModel):
    human_like: bool = True
    typing_delay_ms: DelayRange
    action_delay_seconds: DelayRange
    scroll_simulation: bool = True
    evolution: EvolutionSettings = Field(default_factory=EvolutionSettings)

class SecurityConfig(BaseModel):
    rotate_user_agent: bool = True
    randomize_sessions: bool = True
    max_errors_per_day: int = 5

class LoggingConfig(BaseModel):
    enabled: bool = True
    save_path: str = "./logs"
    export_csv: bool = True

class NotificationChannel(BaseModel):
    enabled: bool = False

class NotificationsConfig(BaseModel):
    email: NotificationChannel = Field(default_factory=NotificationChannel)
    telegram: NotificationChannel = Field(default_factory=NotificationChannel)

class Secrets(BaseModel):
    linkedin: Dict[str, str] = Field(default_factory=dict)
    telegram: Dict[str, str] = Field(default_factory=dict)
    openai: Dict[str, str] = Field(default_factory=dict)

class LinkedInDailyPostsConfig(BaseModel):
    enabled: bool = True
    time: str = "09:00"
    topics: List[str] = Field(default_factory=list)

class LinkedInEngagementConfig(BaseModel):
    comments_per_day: int = 5
    likes_per_day: int = 15
    follows_per_day: int = 10
    target_profiles: List[str] = Field(default_factory=list)

class LinkedInImageGenConfig(BaseModel):
    enabled: bool = True
    style: str = "professional, modern, tech-themed"

class LinkedInAutomationConfig(BaseModel):
    daily_posts: LinkedInDailyPostsConfig
    engagement: LinkedInEngagementConfig
    image_generation: LinkedInImageGenConfig

class Settings(BaseModel):
    bot: BotConfig
    profile: ProfileConfig
    resume: ResumeConfig
    platforms: PlatformsConfig
    behavior: BehaviorConfig
    security: SecurityConfig
    logging: LoggingConfig
    notifications: NotificationsConfig
    linkedin_automation: Optional[LinkedInAutomationConfig] = None
    secrets: Optional[Secrets] = None


def load_config(config_path: str = "config/settings.yaml", secrets_path: str = "config/secrets.yaml") -> Settings:
    """
    Load and validate the configuration and secrets files.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at {path.absolute()}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not data:
                raise ValueError("Configuration file is empty")
        
        # Load secrets if the file exists
        secrets_file = Path(secrets_path)
        if secrets_file.exists():
            with open(secrets_file, 'r', encoding='utf-8') as sf:
                secrets_data = yaml.safe_load(sf)
                if secrets_data:
                    data['secrets'] = secrets_data

        settings = Settings(**data)
        logger.info("Configuration loaded and validated successfully.")
        return settings

    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise
    except ValidationError as e:
        logger.error(f"Validation error in configuration: {e}")
        raise

if __name__ == "__main__":
    # Test loading
    try:
        cfg = load_config("../config/settings.yaml") # Adjust path for direct run from src
        print(f"Loaded config for role: {cfg.profile.role}")
    except Exception as e:
        print(f"Failed: {e}")
