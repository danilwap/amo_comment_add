# src/app/config.py
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    AMO_CLIENT_ID: str
    AMO_CLIENT_SECRET: str
    AMO_REDIRECT_URI: AnyHttpUrl
    AMO_AUTH_BASE_URL: AnyHttpUrl = "https://www.amocrm.ru"
    AMO_DOMAIN: str

    TOKEN_FILE_PATH: str = "tokens.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
