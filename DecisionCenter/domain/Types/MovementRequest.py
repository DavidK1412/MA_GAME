from pydantic import BaseModel


class MovementRequestType(BaseModel):
    movement: list
