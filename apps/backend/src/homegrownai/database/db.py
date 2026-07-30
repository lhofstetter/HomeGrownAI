import traceback
from types import TracebackType
from typing import Type
from pydantic import SecretStr
from sqlalchemy.engine import create_engine, URL
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from loguru import logger

from homegrownai.exceptions import DatabaseError


class DB:
    def __init__(
        self,
        db_driver: str,
        db_user: str,
        db_password: SecretStr,
        db_host: str,
        db_port: int,
        db_name: str,
    ):
        self.db_url = URL.create(
            db_driver,
            db_user,
            db_password.get_secret_value(),
            db_host,
            db_port,
            db_name,
        )
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )


class DBSession:
    def __init__(self, database: DB):
        self.database = database
        self.session: Session | None = None

    def __enter__(self) -> Session:
        self.session = self.database.SessionLocal()
        return self.session

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        assert (
            self.session is not None
        )  # this should not be possible, as DBSession is a context manager so the session should've been defined at __enter__

        if exc_type is None:
            logger.info("Committed to the database successfully!")
            self.session.commit()
        else:
            logger.error(
                "Exception when attempting to access the database. Please inspect the running code and try again. Aborting changes."
            )
            logger.debug(
                f"Exception Type: {exc_type} Exception Value: {exc_value}\nTraceback:\n {traceback}"
            )
            self.session.rollback()

        self.session.close()


"""
@class Base:
    Forms the base for SQLAlchemy's ORM, so that models used in the database are mapped to actual Python objects.  
"""


class Base(DeclarativeBase):
    pass
