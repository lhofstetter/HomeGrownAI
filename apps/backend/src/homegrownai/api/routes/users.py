from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from orjson import OPT_INDENT_2, dumps
from pwdlib import PasswordHash
from sqlalchemy import or_

from homegrownai.database.conversation import Conversation
from homegrownai.database.db import DBSession
from homegrownai.database.dependencies import get_db_session
from homegrownai.database.memory import Memory
from homegrownai.database.user import User
from homegrownai.schemas.user import UserRegistration
from homegrownai.security.security import CurrentUser, create_access_token

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)],
    session: Annotated[DBSession, Depends(get_db_session)],
) -> dict[str, str]:
    hasher = PasswordHash.recommended()

    with session as db:
        user: User | None = (
            db.query(User)
            .filter(
                or_(
                    User.email == form_data.username.lower(),
                    User.username == form_data.username.lower(),
                )
            )
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not hasher.verify(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(user_id=str(user.id))

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }


@users_router.post("/signup")
async def register_account(
    signup_form: Annotated[UserRegistration, Form()],
    session: Annotated[DBSession, Depends(get_db_session)],
):
    hasher = PasswordHash.recommended()
    new_user = User(
        username=signup_form.username.lower(),
        hashed_password=hasher.hash(signup_form.password),
        email=signup_form.email.lower(),
        registration_date=datetime.now(timezone.utc),
        is_active=True,
    )

    with session as db:
        existing_user: User | None = (
            db.query(User)
            .filter(
                or_(User.email == new_user.email, User.username == new_user.username)
            )
            .first()
        )

        if existing_user != None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username or email is already registered with an account!",
                headers={"WWW-Authenticate": "Bearer"},
            )

        db.add(new_user)
        db.commit()

        access_token = create_access_token(user_id=str(new_user.id))

        return {
            "result": "Account created!",
            "access_token": access_token,
            "token_type": "bearer",
        }


@users_router.get("/memories")
async def get_memories(
    user: CurrentUser, session: Annotated[DBSession, Depends(get_db_session)]
):
    with session as db:
        existing_user: User | None = (
            db.query(User)
            .filter(or_(User.email == user.email, User.username == user.username))
            .first()
        )

        if existing_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token! Please log in again.",
                headers={"WWW-Authenticate": "Bearer token error!"},
            )

        for memory in existing_user.memories:
            m = {}
            m["title"] = memory.title
            m["id"] = memory.id

            yield m


@users_router.get("/memory/{memory_id}")
async def get_memory(
    memory_id: UUID,
    user: CurrentUser,
    session: Annotated[DBSession, Depends(get_db_session)],
):
    with session as db:
        existing_user: User | None = (
            db.query(User)
            .filter(or_(User.email == user.email, User.username == user.username))
            .first()
        )

        if existing_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token! Please log in again.",
                headers={"WWW-Authenticate": "Bearer token error!"},
            )

        memory: Memory | None = (
            db.query(Memory).filter(Memory.id == memory_id)
        ).first()

        if memory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        m = {}

        m["title"] = memory.title
        m["summary"] = memory.summary
        m["content"] = memory.content

        return dumps(m, option=OPT_INDENT_2)


@users_router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user: CurrentUser,
    session: Annotated[DBSession, Depends(get_db_session)],
):
    with session as db:
        existing_user: User | None = (
            db.query(User)
            .filter(or_(User.email == user.email, User.username == user.username))
            .first()
        )

        if existing_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token! Please log in again.",
                headers={"WWW-Authenticate": "Bearer token error!"},
            )

        conversation: Conversation | None = (
            db.query(Conversation).filter(Conversation.id == conversation_id)
        ).first()

        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        for msg in conversation.messages:
            m = {"content": msg.content, "id": msg.id, "model_id": msg.model_id}

            yield m


@users_router.get("/conversations")
async def get_conversations(
    user: CurrentUser, session: Annotated[DBSession, Depends(get_db_session)]
):
    with session as db:
        existing_user: User | None = (
            db.query(User)
            .filter(or_(User.email == user.email, User.username == user.username))
            .first()
        )

        if existing_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token! Please log in again.",
                headers={"WWW-Authenticate": "Bearer token error!"},
            )

        for conversation in existing_user.conversations:
            yield conversation
