from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_env: Literal["development", "production", "test"] = "development"
    gemini_api_key: str = ''
    google_maps_api_key: str = ''

    # LLM settings
    gemini_model: str = "gemini-1.5-flash"
    temperature: float = 0.2

    # Maps settings
    maps_radius_meters: int = 8000  # 8km default search radius
    max_candidates: int = 25
    max_results: int = 10
    fallback_max_candidates: int = 30

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
