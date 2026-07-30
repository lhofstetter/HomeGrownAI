from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from fastapi import APIRouter, Depends

from auth import verify_login

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict[str, str]:
    login_result = await verify_login(form_data.username, form_data.password)

    return login_result


@router.post("/signup")
async def register_account():
    pass
