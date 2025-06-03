from pydantic import BaseModel


class ResponseType(BaseModel):
    type: str
    actions: dict
