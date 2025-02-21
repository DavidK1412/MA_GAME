from .BeliefController import BeliefController
from utils import DatabaseClient, get_average_time_between_state_change, get_repeated_states_count


class IncentiveController(BeliefController):
    def __init__(self, dn_client: DatabaseClient, name: str):
        super().__init__(dn_client, name)

    def update_values(self, game_id: str, config: dict):
        new_values: dict = {
            "T_avg": get_average_time_between_state_change(game_id, self.db_client),
            "C_rep": get_repeated_states_count(game_id, self.db_client)
        }
        self.values = new_values

        return True
