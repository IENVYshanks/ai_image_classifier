from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from functools import lru_cache
from sqlalchemy.ext.declarative import declarative_base

from src.config_env import get_env_path, load_env_file

load_env_file()

Base = declarative_base()

class Settings(BaseSettings):
    DATABASE_HOST : str = "localhost"
    DB_USERNAME : str
    DB_PASSWORD : str
    DB_PORT : int = 5432
    DB_NAME : str
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_STORAGE_BUCKET: str | None = None
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "face_embeddings"

    model_config = SettingsConfigDict(
        env_file=str(get_env_path()),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        return(
            f"postgresql+psycopg2://{self.DB_USERNAME}:"
            f"{self.DB_PASSWORD}@{self.DATABASE_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}?sslmode=require"
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()
