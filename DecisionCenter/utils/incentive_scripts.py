from .DatabaseClient import DatabaseClient
from datetime import datetime, timedelta
from .graph_utils import possible_moves as possible_moves_graph, shortest_path_length

'''
    "T_avg": "Tiempo promedio (segundos) entre cambio de estado en la partida",
    "C_rep": "Cantidad de estados repetidos"
'''

def get_actual_attempt_id(game_id: str, db_client: DatabaseClient) -> str:
    query = "SELECT id FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
    params = (game_id,)
    result = db_client.fetch_results(query, params)
    if not result:
        return None
    return result[0]['id']

def get_average_time_between_state_change(game_id: str, db_client: DatabaseClient) -> float:
    game_attempt_id = get_actual_attempt_id(game_id, db_client)
    if not game_attempt_id:
        return 0
    query = "SELECT * FROM movements WHERE attempt_id = %s AND interuption IS FALSE ORDER BY movement_time ASC;"
    params = (game_attempt_id,)
    result = db_client.fetch_results(query, params)
    # Get average time between state change, result is dict type, the movement_time is the key 'movement_time'
    total_time_diff = timedelta()
    for i in range(1, len(result)):
        time1 = datetime.combine(datetime.today(), result[i-1]['movement_time'])
        time2 = datetime.combine(datetime.today(), result[i]['movement_time'])
        time_diff = time2 - time1
        total_time_diff += time_diff
    if len(result) == 1:
        return 0
    if len(result) - 1 == 0:
        return 0
    avg_time_diff = total_time_diff / (len(result) - 1)
    avg_time_diff_seconds = avg_time_diff.total_seconds()
    
    return avg_time_diff_seconds


def get_repeated_states_count(game_id: str, db_client: DatabaseClient) -> int:
    query = "SELECT movement FROM movements WHERE game_id = %s"
    params = (game_id,)
    result = db_client.fetch_results(query, params)
    # Get repeated states count
    states = []
    repeated_states = 0
    for movement in result:
        if movement['movement'] in states:
            repeated_states += 1
            continue
        states.append(movement['movement'])
    print(f'Repeated states: {repeated_states}')

    return repeated_states

def get_misses_count(game_id: str, db_client: DatabaseClient) -> int:
    game_attempt_id = get_actual_attempt_id(game_id, db_client)
    query = "SELECT count FROM movements_misses WHERE game_attempt_id = %s"
    params = (game_attempt_id,)
    result = db_client.fetch_results(query, params)
    if not result or not result[0]['count']:
        return 0
    # Get misses count
    misses = result[0]['count']
    print(f'Misses: {misses}')

    return misses

def get_buclicity(game_id: str, db_client: DatabaseClient) -> float:
    # get actual movement (last movement, this is the higher "step")
    game_attempt_id = get_actual_attempt_id(game_id, db_client)
    query = "SELECT step, movement FROM movements WHERE attempt_id = %s ORDER BY step DESC LIMIT 1"
    params = (game_attempt_id,)
    result = db_client.fetch_results(query, params)
    # Then get the last "step" number that equals the movement
    query = "SELECT step FROM movements WHERE attempt_id = %s AND movement = %s ORDER BY step DESC LIMIT 2"
    params = (game_attempt_id, result[0]['movement'],)
    result_2 = db_client.fetch_results(query, params)
    # Buclicity is the number resultant of result[0]['step'] - result_2[1]['step']
    if len(result_2) < 2:
        buclicity = 0
    else:
        buclicity = result[0]['step'] - result_2[1]['step']
    # update last_buclicity in game_attempts
    query = "UPDATE game_attempts SET last_buclicity = %s WHERE id = %s"
    params = (buclicity, game_attempt_id,)
    db_client.execute_query(query, params)
    print(f'Buclicity: {buclicity}')

    return buclicity

def get_tries_count(game_id: str, db_client: DatabaseClient) -> int:
    game_attempt_id = get_actual_attempt_id(game_id, db_client)
    # select max(step) from movements where attempt_id = game_attempt_id
    query = "SELECT MAX(step) FROM movements WHERE attempt_id = %s"
    params = (game_attempt_id,)
    result = db_client.fetch_results(query, params)
    if not result or not result[0]['max']:
        return 0
    # Get tries count
    tries = result[0]['max']
    print(f'Tries: {tries}')

    return tries

def get_branch_factor(game_id: str, db_client: DatabaseClient) -> float:
    game_attempt_id = get_actual_attempt_id(game_id, db_client)
    query = "SELECT difficulty_id FROM game_attempts WHERE id = %s"
    params = (game_attempt_id,)
    result = db_client.fetch_results(query, params)
    difficulty_id = result[0]['difficulty_id']

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

    # Obtiene el estado inicial
    query = "SELECT movement FROM movements WHERE attempt_id = %s ORDER BY step ASC LIMIT 1"
    params = (game_attempt_id,)
    result = db_client.fetch_results(query, params)
    initial_state = result[0]['movement']
    initial_state = [int(x) for x in initial_state.split(",")]

    possible_moves = possible_moves_graph(blocks_per_team, blocks_per_team, initial_state)
    P = len(possible_moves)
    S = 0
    for move in possible_moves:
        value = shortest_path_length(blocks_per_team, blocks_per_team, move, final_state)
        S += value if value is not None else 0
        if value is None:
            P -= 1
    if P == 0:
        return 1
    B = S / P

    return B

def get_number_of_assertions(game_id: str, db_client: DatabaseClient) -> int:
    # selecciona el total de movimientos donde is_correct es True
    game_attempt_id = get_actual_attempt_id(game_id, db_client)
    query = "SELECT COUNT(*) FROM movements WHERE attempt_id = %s AND is_correct IS TRUE"
    params = (game_attempt_id,)
    result = db_client.fetch_results(query, params)
    return result[0]['count']
    