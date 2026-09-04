from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from homegrownai.database.db import DB, Base, DBSession

from ..exceptions import (
    EmailAlreadyRegisteredError,
    UserDeletionError,
)

if TYPE_CHECKING:
    from homegrownai.database.conversation import Conversation
    from homegrownai.database.document import Document


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    username: Mapped[str]
    hashed_password: Mapped[str]
    email: Mapped[str]
    registration_date: Mapped[date]
    is_active: Mapped[bool]
    deletion_date: Mapped[date]
    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    documents: Mapped[list[Document]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    custom_model_name: Mapped[str]
    custom_model_instructions: Mapped[str]
    human_name: Mapped[str]


def add_user(database: DB, new_user: User):
    with DBSession(database) as session:
        objects = session.scalars(
            select(User).where(User.email == new_user.email)
        ).all()

        if len(objects) != 0:
            raise EmailAlreadyRegisteredError()
        else:
            session.add(new_user)


def delete_user(database: DB, existing_user: User):
    with DBSession(database) as session:
        user = session.scalars(
            select(User).where(User.email == existing_user.email)
        ).first()

        if user is None:
            raise UserDeletionError()  # @TODO: FIX THIS!
        else:
            session.execute(
                update(User)
                .where(User.email == existing_user.email)
                .values(is_active=False, deletion_date=datetime.now(tz=timezone.utc))
            )
