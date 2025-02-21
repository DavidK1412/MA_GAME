import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from utils import load_json_config, DatabaseClient, get_average_time_between_state_change, get_repeated_states_count
from domain import GameType, ResponseType, MovementRequestType 
from controllers import GameController, IncentiveController, DecisionController
from functools import lru_cache

app = FastAPI()

with open("config.json", "r") as file:
    config = json.load(file)

load_json_config(config)

db = DatabaseClient(
    dbname=config["database"]["PGDATABASE"],
    user=config["database"]["PGUSER"],
    password=config["database"]["PGPASSWORD"],
    host=config["database"]["PGHOST"]
)

db.connect()

game_controller = GameController(db)
beliefs = [IncentiveController(db, "Incentive")]
decision_controller = DecisionController(beliefs, config)

@app.get("/")
@lru_cache()
def read_root():
    return JSONResponse( content=ResponseType(
        message="Welcome to the game API",
        data={ "status": "OK" }
    ).dict(), status_code=200)

@app.post("/new_game")
def new_game(game: GameType):
    try: 
        game_controller.create_game(game)
        return JSONResponse( content=ResponseType(
            message="Juego creado exitosamente",
            data={ "game_id": game.id }
        ).dict(), status_code=201)
    except Exception as e:
        return JSONResponse( content=ResponseType(
            message="Error creando el juego",
            data={ "error": str(e) }
        ).dict(), status_code=500)

@app.post("/game/{game_id}/movement")
def move(game_id: str, movement: MovementRequestType):
    try:
        selected_belief = None
        if game_controller.move(game_id, movement, config):
            selected_belief = decision_controller.make_decision(game_id)
        return JSONResponse( content=ResponseType(
            message="Movimiento creado exitosamente",
            data={ "game_id": game_id, "selected_belief": selected_belief }
        ).dict(), status_code=201)
    except Exception as e:
        return JSONResponse( content=ResponseType(
            message="Error creando el movimiento",
            data={ "error": str(e) }
        ).dict(), status_code=500)
