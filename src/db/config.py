from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field
from functools import lru_cache
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Settings(BaseSettings):
    DATABASE_HOST : str = "localhost"
    DB_USERNAME : str
    DB_PASSWORD : str
    DB_PORT : int = 5432
    DB_NAME : str

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        return(
            f"postgresql+psycopg2://{self.DB_USERNAME}:"
            f"{self.DB_PASSWORD}@{self.DATABASE_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()

