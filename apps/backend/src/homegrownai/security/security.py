from typing import Annotated, Any
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jwt import InvalidTokenError, encode, decode
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer

from homegrownai.database.user import User
from homegrownai.database.dependencies import get_db_session
from homegrownai.schemas.settings import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/login",
)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication error: Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


inactive_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Could not validate credentials; inactive user.",
)


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": str(uuid4()),
    }

    return encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except InvalidTokenError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    return payload


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    payload = decode_access_token(token)

    user_id = payload["sub"]

    with get_db_session() as session:
        user: User = session.get_one(User, user_id)

        if not user.is_active:
            raise inactive_exception
        else:
            return user
