import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from utils import load_json_config, DatabaseClient, get_tries_count
from domain import GameType, ResponseType, MovementRequestType 
from controllers import GameController, FeedbackController, DecisionController, AdviceController, ExplainController, DemonstrateController, AskController
from functools import lru_cache
import random

app = FastAPI()

with open("config.json", "r") as file:
    config = json.load(file)

load_json_config(config)

db = DatabaseClient(
    dbname=config["database"]["PGDATABASE"],
    user=config["database"]["PGUSER"],
    password=config["database"]["PGPASSWORD"],
    host=config["database"]["PGHOST"],
    port=config["database"]["PGPORT"]
)

db.connect()

game_controller = GameController(db)
beliefs = [DemonstrateController(db, "Demonstrate"),
    AdviceController(db, "Advice"),
    FeedbackController(db, "Feedback"),
    ExplainController(db, "Explain"),
    AskController(db, "Ask")
]
decision_controller = DecisionController(beliefs, config)

@app.get("/")
@lru_cache()
def read_root():
    return JSONResponse( content=ResponseType(
        type="status",
        actions={ "status": "OK" }
    ).dict(), status_code=200)

@app.post("/game")
def new_game(game: GameType):
    try: 
        game_controller.create_game(game)
        return JSONResponse( content=ResponseType(
            type="game_created",
            actions={ "game_id": game.game_id }
        ).dict(), status_code=200)
    except Exception as e:
        return JSONResponse( content=ResponseType(
            type="error",
            actions={ "error": str(e) }
        ).dict(), status_code=500)

@app.post("/game/{game_id}")
def move(game_id: str, movement: MovementRequestType):
    try:
        selected_belief = None
        game_controller.start_attempt(game_id, movement)
        if game_controller.move(game_id, movement, config):
            # haz que cada 5 intentos se haga una decision
            tries = get_tries_count(game_id, db)
            if tries % 3 == 0 and tries != 0:
                selected_belief = decision_controller.make_decision(game_id)
                response = selected_belief.action(game_id)
                if isinstance(response, ResponseType):
                    return JSONResponse(content=response.dict(), status_code=200)
                else:
                    return JSONResponse(content=response, status_code=200)
            texts = [
                # Frases motivadoras sencillas
                "¡Muy bien!",
                "¡Tú puedes!",
                "¡Buen trabajo!",
                "¡Sigue así!",
                "¡Lo hiciste bien!",
                "¡Vamos, un paso más!",
                "¡Eso estuvo genial!",
                "¡Confío en ti!",
                "¡Te estás acercando!",
                "¡Qué bien lo estás haciendo!",

                # Recordatorios de reglas simples
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
            return JSONResponse(content=ResponseType(
                type="SPEECH",
                actions={ "text": random.choice(texts) }
            ).dict(), status_code=200)
    except DeprecationWarning as e:
        if e == "e":
            return JSONResponse( content=ResponseType(
                type="SPEECH",
                actions={
                    # si es "Best movement", text será "¡Excelente movimiento!", si es "Final movement", text será "Felicidades, has ganado!"
                    "text": "Comienza tu camino!"
                }
            ).dict(), status_code=200)
        if e == "Final movement":
            return JSONResponse( content=ResponseType(
                type="SPEECH",
                actions={
                    # si es "Best movement", text será "¡Excelente movimiento!", si es "Final movement", text será "Felicidades, has ganado!"
                    "text": "¡Felicidades, has ganado el nivel!"
                }
            ).dict(), status_code=200)
        return JSONResponse( content=ResponseType(
                type="SPEECH",
                actions={
                    # si es "Best movement", text será "¡Excelente movimiento!", si es "Final movement", text será "Felicidades, has ganado!"
                    "text": "¡Excelente movimiento!"
                }
            ).dict(), status_code=200)
    except Exception as e:
        # print full traceback
        import traceback
        print(traceback.format_exc())
        return JSONResponse( content=ResponseType(
            type="error",
            actions={ "error": str(e) }
        ).dict(), status_code=500)

@app.post("/game/{game_id}/miss")
def miss(game_id: str):
    try:
        game_controller.miss(game_id)
        return JSONResponse( content=ResponseType(
            type="miss",
            actions={ "game_id": game_id }
        ).dict(), status_code=200)
    except Exception as e:
        return JSONResponse( content=ResponseType(
            type="error",
            actions={ "error": str(e) }
        ).dict(), status_code=500)

@app.get("/game/{game_id}/best_next")
def best_next(game_id: str):
    try:
        return JSONResponse( content=game_controller.get_best_next(game_id).dict(), status_code=200)
    except Exception as e:
        return JSONResponse( content=ResponseType(
            type="error",
            actions={ "error": str(e) }
        ).dict(), status_code=500)    