from datetime import date
from typing import ByteString, Union

from .role import Role
from .db import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    email: Mapped[str]
    registration_date: Mapped[date]
    roles: Mapped[list[Role]] = relationship(back_populates="user")
    
    def add_role(self, admin_token: ByteString, user_id: Union[int, None] = None) -> bool:
        return True
    
