from pydantic import BaseModel


class UserRegistration(BaseModel):
    username: str
    password: str
    email: str


class Conversation(BaseModel):
    conversationTitle: str
    conversationID: str
    modelID: str | None
    attachments: list[dict[str, str]] | None
