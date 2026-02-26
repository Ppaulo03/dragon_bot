from pydantic_settings import BaseSettings, SettingsConfigDict
from app.utils.logging_config import setup_logging
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

    # --- IMAGE LOGIC ---
    DEFAULT_IMAGE_THRESHOLD: int = 5

    # --- BUCKET CONFIG ---
    BUCKET_ENDPOINT: str = ""
    BUCKET_ACCESS_KEY: str = ""
    BUCKET_SECRET_KEY: str = ""
    BUCKET_NAME: str = "dragon-bot-bucket"
    BUCKET_REGION: str = "us-east-1"

    # --- YAML CONFIG ---
    YAML_CONFIG_PATH: str = "config/triggers.yaml"

    # --- EVOLUTION API ---
    EVOLUTION_URL: str
    EVOLUTION_TOKEN: str
    EVOLUTION_INSTANCE: str = "DGN-BOT"
    EVOLUTION_WEBHOOK_URL: str = "http://localhost:8000/webhook/evolution"
    EVOLUTION_INSTANCE_TOKEN: Optional[str] = None
    EVOLUTION_WEBHOOK_BY_EVENTS: bool = False
    EVOLUTION_WEBHOOK_BASE64: bool = False
    EVOLUTION_WEBHOOK_EVENTS: str = "MESSAGES_UPSERT"

    # ----- Postgres Config -----
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "dragon_bot_db"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


setup_logging()
settings = Settings()
