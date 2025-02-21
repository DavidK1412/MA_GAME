from pydantic import BaseModel


class MovementRequestType(BaseModel):
    id: str
    movement: list
