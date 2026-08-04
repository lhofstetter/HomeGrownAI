"""Record the ORM schema used to bootstrap a new database.

Revision ID: 0001_schema_baseline
Revises:
Create Date: 2026-07-30

"""

from collections.abc import Sequence


revision: str = "0001_schema_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """The current ORM metadata creates the baseline schema."""


def downgrade() -> None:
    """The baseline is a version marker, not a schema-building migration."""
