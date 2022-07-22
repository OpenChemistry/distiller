from typing import List, Optional

from pydantic import AnyHttpUrl, BaseSettings
from schemas import WatchMode


class Settings(BaseSettings):
    API_URL: AnyHttpUrl = "http://localhost:8000/api/v1"
    API_KEY_NAME: str
    API_KEY: str
    WATCH_DIRECTORIES: List[str]
    HOST: Optional[str] = None
    LOG_FILE_PATH: Optional[str] = None
    SYNC: bool = True
    MODE: WatchMode = WatchMode.SCAN_4D_FILES
    MICROSCOPE: str
    POLL: bool = False
    RECURSIVE: bool = False

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
