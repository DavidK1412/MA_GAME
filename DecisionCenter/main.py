import json
from fastapi import FastAPI
from utils import load_json_config, DatabaseClient

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

@app.get("/")
def read_root():
    return {
        "config": db.fetch_results("SELECT * FROM difficulty"),
    }

@app.post("/new_game")
def new_game():
    pass