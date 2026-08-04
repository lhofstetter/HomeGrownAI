from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from pwdlib import PasswordHash
from sqlalchemy import or_
from datetime import datetime

from homegrownai.security.security import create_access_token
from homegrownai.database.db import DBSession
from homegrownai.database.dependencies import get_db_session
from homegrownai.database.user import User
from homegrownai.schemas.user import UserRegistration

users_router = APIRouter(prefix="/users", tags=["users"])

@users_router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)],
    session: Annotated[DBSession, Depends(get_db_session)]
) -> dict[str, str]:
    hasher = PasswordHash.recommended()

    with session as db:
        user: User | None = (
            db.query(User)
            .filter(
                or_(User.email == form_data.username, User.username == form_data.username)
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
    signup_form: UserRegistration,
    session: Annotated[DBSession, Depends(get_db_session)]
):
    hasher = PasswordHash.recommended()
    new_user = User(username=signup_form.username, hashed_password=hasher.hash(signup_form.password), email=signup_form.email, registration_date=datetime.now(), is_active=True)

    with session as db:
        existing_user: User | None = db.query(User).filter(
                or_(User.email == new_user.email, User.username == new_user.username)
                ).first()
        
        if existing_user != None:
            raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Username or email is already registered with an account!",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        db.commit()
        access_token = create_access_token(user_id=str(new_user.id))

        return {
                "result": "Account created!",
                "access_token": access_token,
                "token_type": "bearer",
            }
                
