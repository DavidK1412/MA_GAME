import uuid
from domain.Types import ResponseType
from .BeliefController import BeliefController
from utils import DatabaseClient, incentive_scripts, graph_utils
from uuid import uuid4


class AskController(BeliefController):
    def __init__(self, dn_client: DatabaseClient, name: str):
        super().__init__(dn_client, name)

    def update_values(self, game_id: str, config: dict):
        new_values: dict = {
            "B": incentive_scripts.get_buclicity(game_id, self.db_client),
            "TP": incentive_scripts.get_average_time_between_state_change(game_id, self.db_client),
        }
        self.values = new_values
        print("Ask values: ", new_values)
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
            type="ASK",
            actions={
                "text": "¿Necesitas ayuda en el siguiente movimiento?"
            }
        )
            

        
