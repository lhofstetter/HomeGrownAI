from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel


class UserRegistration(BaseModel):
    username: str
