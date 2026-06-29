from typing import Annotated
from pydantic import AnyUrl, Field, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )

    db_url: str = Field()
    db_passwd: SecretStr = Field()
    model_url: str = Field()
    model_api_key: SecretStr = Field()

settings = Settings()
