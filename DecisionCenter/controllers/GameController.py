from utils import DatabaseClient
from domain import GameType, MovementRequestType


class GameController:
    def __init__(self, dn_client: DatabaseClient):
        self.db_client = dn_client

    def create_game(self, params: GameType):
        query = "INSERT INTO game (id, difficulty_id) VALUES (%s, %s)"
        params = (params.id, params.difficulty_id)
        try:
            result = self.db_client.execute_query(query, params)
        except Exception as e:
            raise Exception(f"Error creating game: {e}")

        return result[0] if result else None

    def get_game_by_id(self, game_id: str):
        query = "SELECT * FROM game WHERE id = %s"
        params = (game_id,)
        result = self.db_client.fetch_results(query, params)

        return result[0] if result else None
    
    
    def move(self, game_id: str, movement: MovementRequestType, config):
        get_max_step_query = "SELECT MAX(step) FROM movements WHERE game_id = %s"
        get_max_step_params = (game_id,)
        try:
            max_step = self.db_client.fetch_results(get_max_step_query, get_max_step_params)[0]['max']
            if not max_step:
                max_step = 0
        except Exception as e:
            max_step = 0
        max_step = int(max_step) + 1
        query = "INSERT INTO movements (id, game_id, step, movement) VALUES (%s, %s, %s, %s)"
        movement.movement = ','.join(movement.movement)
        params = (movement.id, game_id, max_step, movement.movement)
        
        
        try:
            self.db_client.execute_query(query, params)
        except Exception as e:
            raise Exception(f"Error creating movement: {e}")
        
        return True if max_step > 1 else False
