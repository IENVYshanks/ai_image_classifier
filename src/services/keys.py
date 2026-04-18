from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Token(BaseSettings):
    ACCESS_TOKEN_EXPIRE_MINUTES : int
    SECRET_KEY : str
    REFRESH_TOKEN_EXPIRE_DAYS : int

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


@lru_cache
def get_tokens() -> Token:
    return Token()