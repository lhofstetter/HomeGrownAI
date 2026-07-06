from typing import ByteString, Union
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Role(Base):
    __tablename__ = "roles"
    
    idx: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[ByteString]
    human_readable_name: Mapped[str]
    permissions: Mapped[dict[str, bool]] # the bool represents write persmissions. If the name of the column exists in the dictionary, we can assume read permissions

    def read_field(table_name:str, field_name: str) -> Union[str, ByteString, dict, None]:
        pass

    def write_value(table_name: str, field_name: str, value: Union[str, ByteString, dict]) -> bool:
        pass
