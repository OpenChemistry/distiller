from typing import List, Optional

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
    SFAPI_SUBMIT_TIME_FORMAT: str
    SFAPI_TZ: str

    ACQUISITION_USER: str
    JOB_COUNT_SCRIPT_PATH: str
    JOB_NCEMHUB_RAW_DATA_PATH: str
    JOB_NCEMHUB_COUNT_DATA_PATH: str
    JOB_SCRIPT_DIRECTORY: str
    JOB_BBCP_NUMBER_OF_STREAMS: int
    JOB_QOS: str
    JOB_QOS_FILTER: str
    JOB_BBCP_EXECUTABLE_PATH: str
    JOB_MACHINE_OVERRIDES_PATH: Optional[str]

    IMAGE_UPLOAD_DIR: str
    HAADF_IMAGE_UPLOAD_DIR_EXPIRATION_HOURS: int
    HAADF_NCEMHUB_DM4_DATA_PATH: str
    NCEMHUB_PATH: str
    NCEMHUB_DATA_PATH: str
    STREAMING_CONFIG_FILEPATH: Optional[str]

    # Max age a scan can be to still have a HAADF metadata associated with it (hours)
    # This is need to avoid associate a metadata with a old scan if the scan ids
    # have been reset in the detector software.
    HAADF_METADATA_SCAN_AGE_LIMIT: int = 1

    CUSTODIAN_USER: str
    CUSTODIAN_PRIVATE_KEY: str
    CUSTODIAN_VALID_HOSTS: List[str] = []

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
