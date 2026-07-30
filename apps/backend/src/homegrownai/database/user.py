from datetime import date
from typing import ByteString
from uuid import UUID as UUID_Rand
from uuid import uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy import select, Engine, insert, update
from sqlalchemy.dialects.postgresql import UUID

from .db import Base, DB, DBSession
from ..exceptions import (
    UserRegistrationError,
    EmailAlreadyRegisteredError,
    UserDeletionError,
)


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
                .values(is_active=False, deletion_date=date.today())
            )
