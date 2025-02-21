from pydantic import BaseModel


class ResponseType(BaseModel):
    data: dict
    message: str
