from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "info"
    RATE_LIMIT: str = "20/minute"

    REDIS_URL: str = "redis://localhost:6379/0"
    RESULT_REDIS_URL: str = "redis://localhost:6379/1"
    RESULT_CACHE_TTL_SECONDS: int = 86400

    GITHUB_TOKEN: str | None = None
    MAX_FILES_PER_PR: int = 200

    USE_OLLAMA: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    ALLOWED_ORIGINS: str = "*"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
