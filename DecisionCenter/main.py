import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from utils import load_json_config, DatabaseClient, get_average_time_between_state_change, get_repeated_states_count
from domain import GameType, ResponseType, MovementRequestType 
from controllers import GameController, FeedbackController, DecisionController, AdviceController, ExplainController, DemonstrateController
from functools import lru_cache

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
            selected_belief = decision_controller.make_decision(game_id)
            response = selected_belief.action(game_id)
            if isinstance(response, ResponseType):
                return JSONResponse(content=response.dict(), status_code=200)
            else:
                return JSONResponse(content=response, status_code=200)
    except DeprecationWarning as e:
        return JSONResponse( content=ResponseType(
                type="SPEECH",
                actions={
                    "text": "De momento todo perfecto, mucho ánimo!"
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