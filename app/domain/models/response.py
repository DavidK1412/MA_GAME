"""
Response domain models.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union
from enum import Enum


class ResponseType(str, Enum):
    """Types of API responses."""
    STATUS = "status"
    GAME_CREATED = "game_created"
    SPEECH = "SPEECH"
    CHANGE_DIFF = "CHANGE_DIFF"
    BEST_NEXT = "BEST_NEXT"
    ERROR = "error"
    MISS = "miss"


class ActionType(str, Enum):
    """Types of actions that can be performed."""
    TEXT = "text"
    GAME_ID = "game_id"
    LEVEL_CHANGE = "level_plus"
    BEST_MOVE = "best_next"
    ERROR = "error"


class Response(BaseModel):
    """Standard API response model."""
    type: ResponseType
    actions: Dict[str, Any] = Field(..., description="Response actions/data")
    message: Optional[str] = None
    timestamp: Optional[str] = None
    
    class Config:
        use_enum_values = True


class SpeechResponse(Response):
    """Speech response for game feedback."""
    type: ResponseType = ResponseType.SPEECH
    actions: Dict[str, str] = Field(..., description="Speech actions")
    
    @classmethod
    def create_encouragement(cls, text: str) -> 'SpeechResponse':
        """Create an encouragement speech response."""
        return cls(
            actions={"text": text},
            message="Encouragement message"
        )
    
    @classmethod
    def create_rule_reminder(cls, text: str) -> 'SpeechResponse':
        """Create a rule reminder speech response."""
        return cls(
            actions={"text": text},
            message="Rule reminder"
        )


class GameResponse(Response):
    """Game-related response."""
    type: ResponseType
    actions: Dict[str, Union[str, int, bool]]
    
    @classmethod
    def game_created(cls, game_id: str) -> 'GameResponse':
        """Create a game created response."""
        return cls(
            type=ResponseType.GAME_CREATED,
            actions={"game_id": game_id}
        )
    
    @classmethod
    def difficulty_changed(cls, text: str, level_change: int) -> 'GameResponse':
        """Create a difficulty change response."""
        return cls(
            type=ResponseType.CHANGE_DIFF,
            actions={
                "text": text,
                "level_plus": level_change
            }
        )


class ErrorResponse(Response):
    """Error response model."""
    type: ResponseType = ResponseType.ERROR
    actions: Dict[str, str] = Field(..., description="Error details")
    
    @classmethod
    def create_error(cls, error_message: str) -> 'ErrorResponse':
        """Create an error response."""
        return cls(
            actions={"error": error_message},
            message="An error occurred"
        )
