from pwdlib import PasswordHash
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from homegrownai.security.security import create_access_token
from homegrownai.main import db as Database
from homegrownai.database.db import DBSession
from homegrownai.database.user import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
async def verify_login(
    username_or_email: str, proposed_password: str
) -> dict[str, str]:
    hasher = PasswordHash.recommended()

    with DBSession(Database) as db:
        user: User | None = (
            db.query(User)
            .filter(
                User.email == username_or_email or User.username == username_or_email
            )
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not hasher.verify(proposed_password, user.hashed_password):
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
