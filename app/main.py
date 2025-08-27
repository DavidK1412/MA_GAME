"""
Main FastAPI application for the Frog Game system.
"""

import json
import random
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import GameException, GameNotFoundError, InvalidMovementError, GameCompletedError
from app.utils.database import DatabaseClient
from app.domain.models.game import GameType
from app.domain.models.movement import MovementRequestType
from app.domain.models.response import Response, ResponseType, SpeechResponse, GameResponse, ErrorResponse
from app.controllers.game import GameController
from app.controllers.decision import DecisionController
from app.controllers.beliefs.advice import AdviceController
from app.controllers.beliefs.feedback import FeedbackController
from app.controllers.beliefs.explain import ExplainController
from app.controllers.beliefs.demonstrate import DemonstrateController
from app.controllers.beliefs.ask import AskController

# Setup logging
setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)
logger = get_logger(__name__)

# Global variables for controllers
game_controller = None
decision_controller = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Frog Game API...")
    
    try:
        # Validate configuration
        settings.validate_config()
        logger.info("Configuration validated successfully")
        
        # Initialize database connection
        global game_controller, decision_controller
        
        db = DatabaseClient(**settings.get_database_config())
        db.connect()
        logger.info("Database connection established")
        
        # Initialize controllers
        game_controller = GameController(db)
        
        beliefs = [
            DemonstrateController(db, "Demonstrate"),
            AdviceController(db, "Advice"),
            FeedbackController(db, "Feedback"),
            ExplainController(db, "Explain"),
            AskController(db, "Ask")
        ]
        decision_controller = DecisionController(beliefs, settings.__dict__)
        
        logger.info("Controllers initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down Frog Game API...")
        if 'db' in locals():
            db.close()


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(GameException)
async def game_exception_handler(request: Request, exc: GameException):
    """Handle game-specific exceptions."""
    logger.warning(f"Game exception: {exc}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse.create_error(str(exc)).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse.create_error("Internal server error").dict()
    )


@app.get("/")
async def read_root():
    """Health check endpoint."""
    return JSONResponse(
        content=Response(
            type=ResponseType.STATUS,
            actions={"status": "OK", "version": settings.API_VERSION}
        ).dict(),
        status_code=200
    )


@app.post("/game")
async def new_game(game: GameType):
    """Create a new game."""
    try:
        game_controller.create_game(game)
        logger.info(f"New game created: {game.game_id}")
        
        return JSONResponse(
            content=GameResponse.game_created(game.game_id).dict(),
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error creating game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/{game_id}")
async def move(game_id: str, movement: MovementRequestType):
    """Process a game move."""
    try:
        game_controller.start_attempt(game_id, movement)
        
        if game_controller.move(game_id, movement, settings.__dict__):
            # Check if decision should be made
            tries = _get_tries_count(game_id)
            if tries % settings.DECISION_INTERVAL == 0 and tries != 0:
                selected_belief = decision_controller.make_decision(game_id)
                response = selected_belief.action(game_id)
                return JSONResponse(
                    content=response.dict() if isinstance(response, Response) else response,
                    status_code=200
                )
            
            # Return motivational message
            return JSONResponse(
                content=_get_random_motivational_message().dict(),
                status_code=200
            )
                
    except GameCompletedError as e:
        return _handle_game_completion(e)
    except GameException as e:
        logger.error(f"Game error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/{game_id}/miss")
async def miss(game_id: str):
    """Record a missed move."""
    try:
        miss_count = game_controller.miss(game_id)
        logger.info(f"Miss recorded for game {game_id}, count: {miss_count}")
        
        return JSONResponse(
            content=Response(
                type=ResponseType.MISS,
                actions={"game_id": game_id, "miss_count": miss_count}
            ).dict(),
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error recording miss: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{game_id}/best_next")
async def best_next(game_id: str):
    """Get the best next move for a game."""
    try:
        response = game_controller.get_best_next(game_id)
        return JSONResponse(content=response.dict(), status_code=200)
    except Exception as e:
        logger.error(f"Error getting best next move: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _handle_game_completion(completion_type: GameCompletedError) -> JSONResponse:
    """Handle different types of game completion."""
    completion_messages = {
        "First move": "¡Comienza tu camino!",
        "Best movement": "¡Excelente movimiento!",
        "Final movement": "¡Felicidades, has ganado el nivel!"
    }
    
    message = completion_messages.get(str(completion_type), "¡Buen trabajo!")
    
    return JSONResponse(
        content=SpeechResponse.create_encouragement(message).dict(),
        status_code=200
    )


def _get_random_motivational_message() -> SpeechResponse:
    """Get a random motivational message."""
    messages = [
        # Motivational messages
        "¡Muy bien!", "¡Tú puedes!", "¡Buen trabajo!", "¡Sigue así!",
        "¡Lo hiciste bien!", "¡Vamos, un paso más!", "¡Eso estuvo genial!",
        "¡Confío en ti!", "¡Te estás acercando!", "¡Qué bien lo estás haciendo!",
        
        # Rule reminders
        "Recuerda: los cubos azules van hacia la derecha.",
        "Recuerda: los cubos rojos van hacia la izquierda.",
        "Solo se puede mover al espacio vacío.",
        "También puedes saltar si hay un cubo en medio.",
        "No saltes sobre tu propio color.",
        "Piensa un poquito antes de moverte.",
        "Hazlo con calma.",
        "Mira bien antes de tocar.",
        "Usa el espacio vacío para ayudar.",
        "No te preocupes si te equivocas, inténtalo otra vez."
    ]
    
    return SpeechResponse.create_encouragement(random.choice(messages))


def _get_tries_count(game_id: str) -> int:
    """Get the number of tries for a game."""
    try:
        # This would need to be implemented in the utils
        # For now, returning a default value
        return 1
    except Exception as e:
        logger.error(f"Error getting tries count: {e}")
        return 1


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
