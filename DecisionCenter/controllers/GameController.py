from utils import DatabaseClient


class GameController:
    def __init__(self, dn_client: DatabaseClient):
        self.db_client = dn_client

    def create_game(self, params: dict):
        query = "INSERT INTO game (id, difficulty_id, created_at, init_time) VALUES (%s, %s, %s, %s) RETURNING id"
        params = (params["id"], params["difficulty_id"], params["created_at"], params["init_time"])
        result = self.db_client.fetch_results(query, params)

        return result[0]["id"] if result else None

    def get_game_by_id(self, game_id: str):
        query = "SELECT * FROM game WHERE id = %s"
        params = (game_id,)
        result = self.db_client.fetch_results(query, params)

        return result[0] if result else None
