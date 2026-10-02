from typing import Literal

from pydantic import BaseModel


class ServerHealthModel(BaseModel):
    status: Literal["ok"]
    version: str
