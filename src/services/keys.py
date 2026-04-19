from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Token(BaseSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES : int
    SECRET_KEY : str
    REFRESH_TOKEN_EXPIRE_DAYS : int
    GOOGLE_CLIENT_ID: str  # Example: "123456789-abcdef.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str  # Example: "GOCSPX-abc123def456"
    GOOGLE_DRIVE_FOLDER_ID: str  # Example: "1A1b2C3d4E5f6G7h8I9j0K"

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


@lru_cache
def get_tokens() -> Token:
    return Token()