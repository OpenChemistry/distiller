from pydantic import AnyHttpUrl, BaseSettings


class Settings(BaseSettings):
    API_URL: AnyHttpUrl = "http://localhost:8000/api/v1"
    API_KEY_NAME: str
    API_KEY: str
    KAFKA_URL: str

    SFAPI_CLIENT_ID: str
    SFAPI_PRIVATE_KEY: str
    SFAPI_GRANT_TYPE: str
    SFAPI_USER: str

    ACQUISITION_USER: str
    JOB_NUMBER_OF_NODES: int
    JOB_COUNT_SCRIPT_PATH: str
    JOB_NUMBER_OF_NODES: int
    JOB_NCEMHUB_RAW_DATA_PATH: str
    JOB_NCEMHUB_COUNT_DATA_PATH: str
    JOB_SCRIPT_DIRECTORY: str

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
