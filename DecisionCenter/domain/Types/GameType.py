from pydantic import BaseModel


class GameType(BaseModel):
    id: str
    difficulty_id: int
    created_at: str
    init_time: str
