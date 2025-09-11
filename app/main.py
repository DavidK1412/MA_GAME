"""
Main FastAPI application for the Frog Game system.
"""

import json
import random
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from core.logging import setup_logging, get_logger
from core.exceptions import GameException, GameNotFoundError, InvalidMovementError, GameCompletedError
from utils.database import DatabaseClient
from domain.models.game import GameType
from domain.models.movement import MovementRequestType
from domain.models.response import Response, ResponseType, SpeechResponse, GameResponse, ErrorResponse
from controllers.game import GameController
from controllers.decision import DecisionController
from controllers.beliefs.advice import AdviceController
from controllers.beliefs.feedback import FeedbackController
from controllers.beliefs.explain import ExplainController
from controllers.beliefs.demonstrate import DemonstrateController
from controllers.beliefs.ask import AskController

# Setup logging
setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)
logger = get_logger(__name__)

# Global variables for controllers

    # Validate configuration
settings.validate_config()
logger.info("Configuration validated successfully")

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

config = settings.get_config()
decision_controller = DecisionController(beliefs, config)

logger.info("Controllers initialized successfully")



# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
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
    logger.info(f"Processing move for game {game_id}: {movement.movement}")
    try:
        logger.info(f"Processing move for game {game_id}: {movement.movement}")
        logger.info(game_controller)

        result = game_controller.move(game_id, movement, config)
        
        # Si need_correct es True, solo se guardó el movimiento, devolver confirmación simple
        if result == "movement_saved":
            logger.info(f"Movement saved only for game {game_id} (need_correct=True)")
            response_content = Response(
                type=ResponseType.STATUS,
                actions={"message": "Movimiento guardado correctamente", "saved": True}
            ).dict()
            
            return JSONResponse(
                content=response_content,
                status_code=200
            )
        
        # Si el controlador devuelve un Response (por ejemplo, cambio de dificultad), responder de inmediato
        if isinstance(result, Response):
            return JSONResponse(content=result.dict(), status_code=200)

        if result:
            # Evaluar y loggear creencias SIEMPRE para debug
            try:
                decision_controller.evaluate_beliefs(game_id)
            except Exception as e:
                logger.error(f"Error evaluating beliefs for debug: {e}")

            # Siempre ejecutar decisión y devolver respuesta de la creencia ganadora
            try:
                selected_belief = decision_controller.make_decision(game_id)
                logger.info(f"🚀 EJECUTANDO ACCIÓN: {selected_belief.name}")
                
                response = selected_belief.action(game_id)
                
                # Log del tipo de respuesta
                if isinstance(response, Response):
                    response_type = response.type if hasattr(response, 'type') else 'Unknown'
                    logger.info(f"✅ RESPUESTA GENERADA: {response_type} - {selected_belief.name}")
                else:
                    logger.info(f"✅ RESPUESTA GENERADA: {type(response).__name__} - {selected_belief.name}")
                
                # Preparar contenido JSON para envío
                json_content = response.dict() if isinstance(response, Response) else response
                
                # Log detallado del JSON que se envía
                import json
                try:
                    json_str = json.dumps(json_content, indent=2, ensure_ascii=False)
                    logger.info(f"📤 JSON ENVIADO AL JUEGO:\n{json_str}")
                except Exception as e:
                    logger.warning(f"Error serializando JSON para log: {e}")
                    logger.info(f"📤 CONTENIDO ENVIADO: {json_content}")
                
                return JSONResponse(
                    content=json_content,
                    status_code=200
                )
            except Exception as e:
                logger.error(f"Error executing belief action: {e}")
                fallback_response = _get_random_motivational_message()
                fallback_content = fallback_response.dict()
                
                # Log del JSON de fallback
                import json
                try:
                    json_str = json.dumps(fallback_content, indent=2, ensure_ascii=False)
                    logger.info(f"📤 JSON FALLBACK ENVIADO:\n{json_str}")
                except Exception as json_e:
                    logger.warning(f"Error serializando JSON fallback: {json_e}")
                    logger.info(f"📤 CONTENIDO FALLBACK: {fallback_content}")
                
                return JSONResponse(
                    content=fallback_content,
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
        
        response_content = Response(
            type=ResponseType.MISS,
            actions={"game_id": game_id, "miss_count": miss_count}
        ).dict()
        
        # Log del JSON de miss
        import json
        try:
            json_str = json.dumps(response_content, indent=2, ensure_ascii=False)
            logger.info(f"📤 JSON MISS ENVIADO:\n{json_str}")
        except Exception as e:
            logger.warning(f"Error serializando JSON de miss: {e}")
            logger.info(f"📤 CONTENIDO MISS: {response_content}")
        
        return JSONResponse(
            content=response_content,
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
        response_content = response.dict()
        
        # Log del JSON de best_next
        import json
        try:
            json_str = json.dumps(response_content, indent=2, ensure_ascii=False)
            logger.info(f"📤 JSON BEST_NEXT ENVIADO:\n{json_str}")
        except Exception as e:
            logger.warning(f"Error serializando JSON de best_next: {e}")
            logger.info(f"📤 CONTENIDO BEST_NEXT: {response_content}")
        
        return JSONResponse(content=response_content, status_code=200)
    except Exception as e:
        logger.error(f"Error getting best next move: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _handle_game_completion(completion_type: GameCompletedError) -> JSONResponse:
    """Handle different types of game completion."""
    import random
    
    if str(completion_type) == "Best movement":
        best_movement_messages = [
            "¡Excelente movimiento!",
            "¡Perfecto! Ese fue un gran paso.",
            "¡Fantástico! Estás dominando el juego.",
            "¡Increíble! Qué movimiento tan inteligente.",
            "¡Genial! Estás mejorando mucho.",
            "¡Magnífico! Ese movimiento fue perfecto.",
            "¡Brillante! Tu estrategia es excelente.",
            "¡Impresionante! Estás jugando muy bien.",
            "¡Sobresaliente! Ese fue un movimiento maestro.",
            "¡Extraordinario! Tu habilidad mejora cada vez más.",
            "¡Maravilloso! Ese movimiento fue estratégico.",
            "¡Excepcional! Estás desarrollando gran destreza.",
            "¡Phenomenal! Tu juego es cada vez mejor.",
            "¡Sensacional! Ese movimiento fue perfecto.",
            "¡Estupendo! Estás convirtiéndote en un experto."
        ]
        message = random.choice(best_movement_messages)
    else:
        if str(completion_type) == "Final movement":
            # Mensajes especiales para completar todos los niveles
            final_completion_messages = [
                "¡Felicidades! Has completado todos los niveles del juego! ¡Eres un verdadero maestro!",
                "¡Increíble! Has conquistado todos los niveles. ¡Eres un experto en el juego de las ranas!",
                "¡Fantástico! Has superado todos los desafíos. ¡Eres un campeón del juego!",
                "¡Magnífico! Has dominado todos los niveles. ¡Tu habilidad es excepcional!",
                "¡Brillante! Has completado el juego completo. ¡Eres un verdadero estratega!",
                "¡Sobresaliente! Has vencido todos los niveles. ¡Tu perseverancia es admirable!",
                "¡Extraordinario! Has terminado todos los desafíos. ¡Eres un maestro del juego!",
                "¡Phenomenal! Has completado toda la aventura. ¡Tu destreza es impresionante!"
            ]
            message = random.choice(final_completion_messages)
        else:
            completion_messages = {
                "First move": "¡Comienza tu camino!"
            }
            message = completion_messages.get(str(completion_type), "¡Buen trabajo!")
        
        response_content = SpeechResponse.create_encouragement(message).dict()
    
    # Log del JSON de finalización de juego
    import json
    try:
        json_str = json.dumps(response_content, indent=2, ensure_ascii=False)
        logger.info(f"📤 JSON FINALIZACIÓN DE JUEGO:\n{json_str}")
    except Exception as e:
        logger.warning(f"Error serializando JSON de finalización: {e}")
        logger.info(f"📤 CONTENIDO FINALIZACIÓN: {response_content}")
    
    return JSONResponse(
        content=response_content,
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
        return game_controller.get_tries_count(game_id)
    except Exception as e:
        logger.error(f"Error getting tries count: {e}")
        return 0


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
