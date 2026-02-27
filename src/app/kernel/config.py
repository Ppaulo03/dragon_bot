from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- APP CONFIG ---
    ENV: str = "dev"
    DEBUG: bool = True

    # --- TRANSLATE SERVICE ---
    TRANSLATE_URL: Optional[str] = None
    TRANSLATE_API_KEY: Optional[str] = None
    TRANSLATE_TIMEOUT: int = 10
    TRANSLATE_TARGET_LANG: str = "pb"

    # --- BUCKET CONFIG ---
    BUCKET_ENDPOINT: str = ""
    BUCKET_ACCESS_KEY: str = ""
    BUCKET_SECRET_KEY: str = ""
    BUCKET_NAME: str = "dragon-bot-bucket"
    BUCKET_REGION: str = "us-east-1"

    # --- EVOLUTION API ---
    EVOLUTION_URL: str
    EVOLUTION_TOKEN: str
    EVOLUTION_INSTANCE: str = "DGN-BOT"
    EVOLUTION_WEBHOOK_URL: str = "http://localhost:8000/webhook/evolution"
    EVOLUTION_INSTANCE_TOKEN: Optional[str] = None
    EVOLUTION_WEBHOOK_BY_EVENTS: bool = False
    EVOLUTION_WEBHOOK_BASE64: bool = False
    EVOLUTION_WEBHOOK_EVENTS: str = "MESSAGES_UPSERT"

    SETTINGS_PATH: str = "config"


settings = Settings()
