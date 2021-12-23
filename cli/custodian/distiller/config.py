from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    SCAN_DIRECTORIES: List[str]
    LOG_FILE_PATH: str = None

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
