from pydantic import AnyHttpUrl, BaseSettings


class Settings(BaseSettings):
    API_URL: AnyHttpUrl = "http://localhost:8000/api/v1"
    API_KEY_NAME: str
    API_KEY: str
    KAFKA_URL: str

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
