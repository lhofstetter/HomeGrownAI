from pydantic import BaseModel, Field
from typing import List, ByteString, Dict, Annotated, Tuple, Union

class Role(BaseModel):
    id: Annotated[ByteString, Field(strict=True)]
    human_readable_name: Annotated[str, Field(strict=True)]
    tables: Annotated[List[str], Field(strict=True)]
    fields: Annotated[Dict[str, bool], Field(strict=True)] # the bool represents write persmissions. If the name of the field exists in the dictionary, we can assume read permissions

    def read_field(table_name:str, field_name: str) -> Union[str, ByteString, Dict, ByteString, None]:
        pass

    def write_value(table_name: str, field_name: str, value: Union[str, ByteString, Dict, ByteString]) -> bool:
        pass
