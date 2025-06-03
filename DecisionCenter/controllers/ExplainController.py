import uuid
from domain.Types import ResponseType
from .BeliefController import BeliefController
from utils import DatabaseClient, incentive_scripts
from uuid import uuid4


class ExplainController(BeliefController):
    def __init__(self, dn_client: DatabaseClient, name: str):
        super().__init__(dn_client, name)

    def update_values(self, game_id: str, config: dict):
        new_values: dict = {
            "CE": (1 - (incentive_scripts.get_tries_count(game_id, self.db_client) / incentive_scripts.get_branch_factor(game_id, self.db_client))) * (1 - (incentive_scripts.get_misses_count(game_id, self.db_client) / 10)),
            "E": incentive_scripts.get_misses_count(game_id, self.db_client)
        }
        self.values = new_values
        print("Explain values: ", new_values)
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
        
        return ResponseType(
            type="TUTORIAL",
            actions={
                "text": "Con este video seguramente entenderás mejor el juego",
                "video": "VIDEO2.MP4"
            }
        )