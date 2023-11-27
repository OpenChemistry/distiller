from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SCAN_DIRECTORIES: List[str]
    LOG_FILE_PATH: str = None
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
