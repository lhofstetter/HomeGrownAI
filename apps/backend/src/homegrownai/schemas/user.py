from typing import Annotated, Optional

from pydantic import BaseModel


class UserRegistration(BaseModel):
    username: str
    password: str
    email: str


class Conversation(BaseModel):
    conversationTitle: str
    conversationID: str
    modelID: Optional[str]
    attachments: Optional[list[str]]
