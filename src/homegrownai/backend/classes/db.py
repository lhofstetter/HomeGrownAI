from pydantic import SecretStr

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase


class DB:
    def __init__(self, engine_url: str, user: str, password: SecretStr):
        self.engine = create_engine(engine_url.replace("user", user))
        self.user = user
        self.db_password = password


class Base(DeclarativeBase):
    pass
