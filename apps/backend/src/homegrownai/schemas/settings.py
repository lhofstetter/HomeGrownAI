from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_driver: str
    db_user: str
    db_passwd: SecretStr
    db_host: str
    db_port: int
    db_name: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    test_user: str
    test_password: str
    access_token_expire_minutes: int = 15
    degoog_docker_passwd: SecretStr
    degoog_docker_db_passwd: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env",
    )


settings = Settings()
