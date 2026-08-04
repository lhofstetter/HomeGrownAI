"""Create a fresh schema or migrate an Alembic-managed schema to head."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect

from .dependencies import db
from .models import Base

ALEMBIC_VERSION_TABLE = "alembic_version"
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_alembic_config() -> Config:
    """Load logging from alembic.ini and migration paths from pyproject.toml."""
    return Config(
        file_=PROJECT_ROOT / "alembic.ini",
        toml_file=PROJECT_ROOT / "pyproject.toml",
    )


def ensure_database_schema(engine: Engine | None = None) -> None:
    """Build a blank database or upgrade an existing managed database."""
    target_engine = engine or db.engine
    alembic_config = get_alembic_config()

    with target_engine.begin() as connection:
        table_names = set(inspect(connection).get_table_names())
        alembic_config.attributes["connection"] = connection

        if not table_names:
            Base.metadata.create_all(connection)
            command.stamp(alembic_config, "head")
            return

        if ALEMBIC_VERSION_TABLE not in table_names:
            raise RuntimeError(
                "The database is not empty and is not managed by Alembic. "
                "Refusing to stamp it as current without verifying its schema."
            )

        command.upgrade(alembic_config, "head")
