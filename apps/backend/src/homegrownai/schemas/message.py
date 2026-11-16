from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel, Field


class Message(BaseModel):
    message: str
    model_id: UUID
    file: UploadFile | None = Field(default=None)
