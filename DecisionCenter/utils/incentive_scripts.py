from .DatabaseClient import DatabaseClient
from datetime import datetime, timedelta

'''
    "T_avg": "Tiempo promedio (segundos) entre cambio de estado en la partida",
    "C_rep": "Cantidad de estados repetidos"
'''

def get_average_time_between_state_change(game_id: str, db_client: DatabaseClient) -> float:
    query = "SELECT * FROM movements WHERE game_id = %s ORDER BY movement_time ASC;"
    params = (game_id,)
    result = db_client.fetch_results(query, params)
    # Get average time between state change, result is dict type, the movement_time is the key 'movement_time'
    total_time_diff = timedelta()
    for i in range(1, len(result)):
        time1 = datetime.combine(datetime.today(), result[i-1]['movement_time'])
        time2 = datetime.combine(datetime.today(), result[i]['movement_time'])
        time_diff = time2 - time1
        total_time_diff += time_diff

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