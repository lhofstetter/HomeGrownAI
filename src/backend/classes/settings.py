from typing import Annotated
from pydantic import AnyUrl, Field, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )
    database_url: str
    database_password: SecretStr 
    model_url: str
    model_api_key: SecretStr 
