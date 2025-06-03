import uuid
from domain.Types import ResponseType
from .BeliefController import BeliefController
from utils import DatabaseClient, incentive_scripts, graph_utils
from uuid import uuid4


class DemonstrateController(BeliefController):
    def __init__(self, dn_client: DatabaseClient, name: str):
        super().__init__(dn_client, name)

    def update_values(self, game_id: str, config: dict):
        new_values: dict = {
            "IP": incentive_scripts.get_tries_count(game_id, self.db_client),
            "TPM": incentive_scripts.get_average_time_between_state_change(game_id, self.db_client),
            "A": incentive_scripts.get_number_of_assertions(game_id, self.db_client)
        }
        self.values = new_values
        print("Advice values: ", new_values)
        return True
    
    def action(self, game_id: str):
        # Update last movement in movements table, to mark it with interuption = True. Unicamente tengo el game_id
        get_actual_game_attemp_query = "SELECT * FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
        get_actual_game_attemp_params = (game_id,)
        actual_game_attemp = self.db_client.fetch_results(get_actual_game_attemp_query, get_actual_game_attemp_params)[0]
        attempt_id = actual_game_attemp['id']
        query = "UPDATE movements SET interuption = TRUE WHERE attempt_id = %s AND step = (SELECT MAX(step) FROM movements WHERE attempt_id = %s)"
        params = (attempt_id, attempt_id)
        self.db_client.execute_query(query, params)
        # obtiene el movimiento anterior al actual
        query = "SELECT * FROM movements WHERE attempt_id = %s AND step = (SELECT MAX(step) FROM movements WHERE attempt_id = %s) - 1"
        params = (attempt_id, attempt_id)
        last_movement = self.db_client.fetch_results(query, params)
        if len(last_movement) == 0:
            return {
                "type": "ERROR",
                "message": "No se encontro movimiento anterior"
            }
        last_movement = last_movement[0]
        difficulty_id = actual_game_attemp['difficulty_id']
        difficulty = {
            1: {
                "blocks_per_team": 3,
                "final_state": [6, 5, 4, 0, 1, 2, 3]
            },
            2: {
                "blocks_per_team": 4,
                "final_state": [8, 7, 6, 5, 0, 1, 2, 3, 4]
            },
            3: {
                "blocks_per_team": 5,
                "final_state": [10, 9, 8, 7, 6, 0, 1, 2, 3, 4, 5]
            }
        }
        difficulty = difficulty[difficulty_id]
        blocks_per_team = difficulty['blocks_per_team']
        final_state = difficulty['final_state']
        last_movement['movement'] = [int(x) for x in last_movement['movement'].split(",")]

        # obtiene el mejor movimiento
        best_movement = graph_utils.best_next_move(last_movement['movement'], final_state)
        print("Best movement: ", best_movement)
        return {
            "type": "CORRECT",
            "last_state": last_movement['movement'],
            "best_next_state": best_movement
        }

        
