from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True, env_file=".env", extra="ignore"
    )

    SCAN_DIRECTORIES: List[str]
    LOG_FILE_PATH: Optional[str] = None


settings = Settings()
