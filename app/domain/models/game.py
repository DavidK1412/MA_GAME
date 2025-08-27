"""
Game domain models with validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from uuid import UUID


class GameType(BaseModel):
    """Game creation model."""
    game_id: str = Field(..., description="Unique identifier for the game")
    
    @validator('game_id')
    def validate_game_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Game ID cannot be empty')
        return v.strip()


class GameState(BaseModel):
    """Current state of a game."""
    game_id: str
    is_finished: bool = False
    current_attempt_id: Optional[str] = None
    difficulty_level: int = Field(ge=1, le=3, description="Game difficulty level (1-3)")
    total_moves: int = 0
    total_errors: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GameAttempt(BaseModel):
    """Game attempt model."""
    id: str
    game_id: str
    difficulty_id: int = Field(ge=1, le=3)
    is_active: bool = True
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_steps: int = 0
    successful_moves: int = 0
    failed_moves: int = 0
