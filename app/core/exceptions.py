"""
Custom exceptions for the Frog Game system.
"""


class GameException(Exception):
    """Base exception for game-related errors"""
    pass


class GameNotFoundError(GameException):
    """Raised when a game is not found"""
    pass


class InvalidMovementError(GameException):
    """Raised when a movement is invalid"""
    pass


class GameCompletedError(GameException):
    """Raised when trying to modify a completed game"""
    pass


class DatabaseError(GameException):
    """Raised when database operations fail"""
    pass


class ConfigurationError(GameException):
    """Raised when configuration is invalid"""
    pass


class BeliefEvaluationError(GameException):
    """Raised when belief evaluation fails"""
    pass
