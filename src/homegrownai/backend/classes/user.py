from datetime import date
from typing import Annotated, List, ByteString

from role import Role

from pydantic import BaseModel, Field

class User(BaseModel):
    username: Annotated[str, Field(strict=True)]
    email: Annotated[str, Field(strict=True)]
    registration_date: Annotated[date, Field()]
    roles: List[Role]

    def add_role(self, admin_token: ByteString) -> bool:
        return True
    
