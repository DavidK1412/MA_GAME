from pydantic import BaseModel


class GameType(BaseModel):
    game_id: str
