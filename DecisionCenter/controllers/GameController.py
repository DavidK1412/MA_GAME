from utils import DatabaseClient, graph_utils
from domain import GameType, MovementRequestType, ResponseType
import uuid

class GameController:
    def __init__(self, dn_client: DatabaseClient):
        self.db_client = dn_client

    def create_game(self, params: GameType):
        query = "INSERT INTO game (id) VALUES (%s)"
        params = (params.game_id,)
        try:
            result = self.db_client.execute_query(query, params)
        except Exception as e:
            raise Exception(f"Error creating game: {e}")

        return result[0] if result else None


    def get_game_by_id(self, game_id: str):
        query = "SELECT * FROM game WHERE id = %s AND is_finished IS FALSE"
        params = (game_id,)
        result = self.db_client.fetch_results(query, params)

        return result[0] if result else None
    
    def start_attempt(self, game_id: str, movement: MovementRequestType):
        # validate if any attempt is active
        get_actual_game_attemp_query = "SELECT * FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
        get_actual_game_attemp_params = (game_id,)
        actual_game_attemp = self.db_client.fetch_results(get_actual_game_attemp_query, get_actual_game_attemp_params)
        if actual_game_attemp:
            return
        attempt_id = str(uuid.uuid4())
        difficulties = {
            7: 1,
            9: 2,
            11: 3
        }
        difficulty_id = difficulties[len(movement.movement)]
        query = "INSERT INTO game_attempts(id, game_id, difficulty_id) VALUES (%s, %s, %s)"
        params = (attempt_id, game_id, difficulty_id)
        try:
            self.db_client.execute_query(query, params)
            return attempt_id
        except Exception as e:
            raise Exception(f"Error creating attempt: {e}")
        

    def move(self, game_id: str, movement: MovementRequestType, config):
        get_actual_game_attemp_query = "SELECT * FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
        get_max_step_query = "SELECT MAX(step) FROM movements WHERE attempt_id = %s"
        try:
            get_actual_game_attemp_params = (game_id,)
            actual_game_attemp = self.db_client.fetch_results(get_actual_game_attemp_query, get_actual_game_attemp_params)[0]
            get_max_step_params = (actual_game_attemp['id'],)
            max_step = self.db_client.fetch_results(get_max_step_query, get_max_step_params)[0]['max']
            print("test", max_step)
            if not max_step:
                max_step = 0
        except Exception as e:
            max_step = 0
        if max_step >= 1:
            get_last_movement_query = "SELECT * FROM movements WHERE attempt_id = %s ORDER BY step DESC LIMIT 1"
            get_last_movement_params = (actual_game_attemp['id'],)
            difficulty = {
                1: {
                    "blocks_per_team": 3,
                    "final_state": [4, 5, 6, 0, 1, 2, 3]
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
            difficulty = difficulty[actual_game_attemp['difficulty_id']]
            last_movement = self.db_client.fetch_results(get_last_movement_query, get_last_movement_params)[0]
            last_movement['movement'] = [int(x) for x in last_movement['movement'].split(",")]
            best_movement = graph_utils.best_next_move(last_movement['movement'], difficulty['final_state'])
            if best_movement == movement.movement:
                # guarda movimiento como correcto
                query = "INSERT INTO movements (id, attempt_id, step, movement, is_correct) VALUES (%s, %s, %s, %s, %s)"
                movement.movement = [str(item) for item in movement.movement]
                movement.movement = ','.join(movement.movement) 
                movement.movement = movement.movement.replace("{", "").replace("}", "")
                params = (str(uuid.uuid4()), actual_game_attemp['id'], max_step, movement.movement, True)
                self.db_client.execute_query(query, params)
                raise DeprecationWarning("Best movement")
            if movement.movement == difficulty['final_state'] and max_step > 1:
                # guarda el movimiento como correcto y termina el intento
                query = "INSERT INTO movements (id, attempt_id, step, movement, is_correct) VALUES (%s, %s, %s, %s, %s)"
                movement.movement = [str(item) for item in movement.movement]
                movement.movement = ','.join(movement.movement) 
                movement.movement = movement.movement.replace("{", "").replace("}", "")
                params = (str(uuid.uuid4()), actual_game_attemp['id'], max_step, movement.movement, True)
                self.db_client.execute_query(query, params)
                query = "UPDATE game_attempts SET is_active = %s WHERE id = %s"
                params = (False, actual_game_attemp['id'])
                self.db_client.execute_query(query, params)
                raise DeprecationWarning("Final movement")

        max_step = int(max_step) + 1
        movement_id = str(uuid.uuid4())
        movement_attempt_id = actual_game_attemp['id']
        query = "INSERT INTO movements (id, attempt_id, step, movement) VALUES (%s, %s, %s, %s)"
        movement.movement = [str(item) for item in movement.movement]
        movement.movement = ','.join(movement.movement)
        movement.movement = movement.movement.replace("{", "").replace("}", "")
        params = (movement_id, movement_attempt_id, max_step, movement.movement)
        
        try:
            self.db_client.execute_query(query, params) 
        except Exception as e:
            raise Exception(f"Error creating movement: {e}")

        if max_step == 1:
            raise DeprecationWarning("e")
        
        return True if max_step >= 1 else False

    def miss(self, game_id: str):
        get_actual_game_attemp_query = "SELECT * FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
        get_actual_game_attemp_params = (game_id,)
        actual_game_attemp = self.db_client.fetch_results(get_actual_game_attemp_query, get_actual_game_attemp_params)[0]
        attempt_id = actual_game_attemp['id']
        get_counter_query = "SELECT * FROM movements_misses WHERE game_attempt_id = %s"
        get_counter_params = (attempt_id,)
        counter = self.db_client.fetch_results(get_counter_query, get_counter_params)
        if not counter:
            counter = 1
        else:
            counter = counter[0]['count'] + 1
            query = "UPDATE movements_misses SET count = %s WHERE game_attempt_id = %s"
            params = (counter, attempt_id)
            try:
                self.db_client.execute_query(query, params)
                return counter
            except Exception as e:
                raise Exception(f"Error updating movement miss: {e}")
        query = "INSERT INTO movements_misses (id, game_attempt_id, count) VALUES (%s, %s, %s)"
        params = (str(uuid.uuid4()), attempt_id, counter)
        try:
            self.db_client.execute_query(query, params)
        except Exception as e:
            raise Exception(f"Error creating movement miss: {e}")

    def get_best_next(self, game_id: str):
        get_actual_game_attemp_query = "SELECT * FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
        get_actual_game_attemp_params = (game_id,)
        actual_game_attemp = self.db_client.fetch_results(get_actual_game_attemp_query, get_actual_game_attemp_params)[0]
        get_last_movement_query = "SELECT * FROM movements WHERE attempt_id = %s ORDER BY step DESC LIMIT 1"
        get_last_movement_params = (actual_game_attemp['id'],)
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
        difficulty = difficulty[actual_game_attemp['difficulty_id']]
        last_movement = self.db_client.fetch_results(get_last_movement_query, get_last_movement_params)[0]
        last_movement['movement'] = [int(x) for x in last_movement['movement'].split(",")]
        best_movement = graph_utils.best_next_move(last_movement['movement'], difficulty['final_state'])
        return ResponseType(
            type="BEST_NEXT",
            actions={
                "text": "Este es el movimiento correcto",
                "best_next": best_movement
            }
        )
        
        