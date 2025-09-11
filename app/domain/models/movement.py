"""
Movement domain models with validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum


class MovementType(str, Enum):
    """Types of movements in the game."""
    REGULAR = "regular"
    JUMP = "jump"
    BEST_MOVE = "best_move"
    WINNING_MOVE = "winning_move"


class MovementRequestType(BaseModel):
    """Movement request model."""
    movement: list[int]
    need_correct: bool
    
    @validator('movement')
    def validate_movement(cls, v):
        if not v:
            raise ValueError('Movement cannot be empty')
        
        # Validate movement length (7, 9, or 11 positions)
        valid_lengths = [7, 9, 11]
        if len(v) not in valid_lengths:
            raise ValueError(f'Movement must have {valid_lengths} positions, got {len(v)}')
        
        # Validate that all elements are integers
        if not all(isinstance(x, int) for x in v):
            raise ValueError('All movement elements must be integers')
        
        # Validate that there's exactly one empty position (0)
        if v.count(0) != 1:
            raise ValueError('Movement must have exactly one empty position (0)')
        
        return v


class Movement(BaseModel):
    """Movement model."""
    id: str
    attempt_id: str
    step: int = Field(ge=1, description="Step number in the attempt")
    movement: str  # Stored as comma-separated string in DB
    is_correct: bool = False
    movement_type: MovementType = MovementType.REGULAR
    execution_time: Optional[float] = None  # Time taken to execute in seconds
    created_at: Optional[str] = None
    
    def get_movement_list(self) -> List[int]:
        """Convert stored movement string back to list."""
        return [int(x.strip()) for x in self.movement.split(',') if x.strip()]
    
    def set_movement_list(self, movement_list: List[int]) -> None:
        """Convert movement list to string for storage."""
        self.movement = ','.join(str(x) for x in movement_list)


class MovementValidation(BaseModel):
    """Movement validation result."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggested_moves: Optional[List[List[int]]] = None
