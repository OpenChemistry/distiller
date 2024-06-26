import secrets
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, validator

from app.schemas import Machine


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    SERVER_NAME: str
    SERVER_HOST: AnyHttpUrl
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, Literal["*"]]] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    API_KEY_NAME: str
    API_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_COOKIE_DOMAIN: str = None
    JWT_REFRESH_COOKIE_SECURE: bool = False

    KAFKA_BOOTSTRAP_SERVERS: List[str]

    SCAN_FILE_UPLOAD_DIR: str
    IMAGE_UPLOAD_DIR: str
    IMAGE_URL_PREFIX: str
    IMAGE_STATIC_DIR: str
    IMAGE_FORMAT: str = "jpeg"
    # Max age a scan can be to still have a HAADF image associated with it (hours)
    # This is need to avoid associate a HAADF with a old scan if the scan ids
    # have been reset in in the detector software.
    HAADF_SCAN_AGE_LIMIT: int = 1

    SENTRY_DSN_URL: AnyHttpUrl = None

    MACHINES: List[Machine]
    NCEMHUB_PATH: str
    NOTEBOOKS: List[str] = ["DPC", "vacuum_scan_prepare", "vacuum_scan_subtract"]

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
