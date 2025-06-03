from collections import deque
import networkx as nx
from collections import defaultdict


def shortest_path_length(total_left, total_right, start_state, goal_state, max_depth=100):
    def is_left_frog(frog):
        return 1 <= frog <= total_left

    def is_right_frog(frog):
        return total_left < frog <= total_left + total_right

    def is_valid_move(state, i, j):
        frog = state[i]
        if frog == 0:
            return False

        direction = j - i
        if abs(direction) not in [1, 2]:
            return False
        if state[j] != 0:
            return False

        if direction > 0 and is_left_frog(frog):
            if abs(direction) == 2 and is_left_frog(state[i + 1]):
                return False
            return True

        if direction < 0 and is_right_frog(frog):
            if abs(direction) == 2 and is_right_frog(state[i - 1]):
                return False
            return True

        return False

    def generate_neighbors(state):
        neighbors = []
        empty_index = state.index(0)

        for offset in [-2, -1, 1, 2]:
            i = empty_index + offset
            if 0 <= i < len(state):
                if is_valid_move(state, i, empty_index):
                    new_state = state[:]
                    new_state[empty_index], new_state[i] = new_state[i], new_state[empty_index]
                    neighbors.append(new_state)
        return neighbors

    visited = set()
    queue = deque([(start_state, 1)])  # estado y profundidad (longitud del camino)

    while queue:
        current, depth = queue.popleft()
        current_tuple = tuple(current)

        if current == goal_state:
            return depth

        if current_tuple in visited or depth > max_depth:
            continue

        visited.add(current_tuple)

        for neighbor in generate_neighbors(current):
            queue.append((neighbor, depth + 1))

    return None  # No se encontró camino


def possible_moves(total_left, total_right, initial_state):
    def is_left_frog(frog):
        return 1 <= frog <= total_left

    def is_right_frog(frog):
        return total_left < frog <= total_left + total_right

    def is_valid_move(state, i, j):
        frog = state[i]
        if frog == 0:
            return False

        direction = j - i

        if abs(direction) not in [1, 2]:
            return False

        if direction > 0 and is_left_frog(frog):
            if abs(direction) == 2:
                jumped_frog = state[i + 1]
                if is_left_frog(jumped_frog):
                    return False
            return True

        if direction < 0 and is_right_frog(frog):
            if abs(direction) == 2:
                jumped_frog = state[i - 1]
                if is_right_frog(jumped_frog):
                    return False
            return True

        return False

    def generate_neighbors(state):
        neighbors = []
        empty_index = state.index(0)

        for offset in [-2, -1, 1, 2]:
            i = empty_index + offset
            if 0 <= i < len(state):
                if is_valid_move(state, i, empty_index):
                    new_state = state[:]
                    new_state[empty_index], new_state[i] = new_state[i], new_state[empty_index]
                    neighbors.append(new_state)
        return neighbors

    neighbors = generate_neighbors(initial_state)

    return neighbors
    

def best_next_move(initial_state, goal_state):
    def generate_neighbors(state):
        neighbors = []
        empty_index = state.index(0)
        
        # Definir movimientos posibles
        moves = [
            (empty_index - 1, empty_index),  # Mover a la izquierda
            (empty_index - 2, empty_index),  # Saltar a la izquierda
            (empty_index + 1, empty_index),  # Mover a la derecha
            (empty_index + 2, empty_index)   # Saltar a la derecha
        ]
        
        for i, j in moves:
            if 0 <= i < len(state):
                new_state = state[:]
                new_state[j], new_state[i] = new_state[i], new_state[j]
                neighbors.append(new_state)
        return neighbors

    def build_graph(initial_state):
        graph = defaultdict(list)
        queue = [initial_state]
        visited = set()

        while queue:
            current_state = queue.pop(0)
            if tuple(current_state) in visited:
                continue
            visited.add(tuple(current_state))

            neighbors = generate_neighbors(current_state)
            graph[tuple(current_state)] = [tuple(neighbor) for neighbor in neighbors]

            for neighbor in neighbors:
                if tuple(neighbor) not in visited:
                    queue.append(neighbor)
        return graph

    # Construir el grafo desde el estado inicial
    graph_dict = build_graph(initial_state)
    G = nx.DiGraph()
    for state, neighbors in graph_dict.items():
        for neighbor in neighbors:
            G.add_edge(state, neighbor)

    # Obtener camino más corto
    try:
        shortest_path = nx.shortest_path(G, source=tuple(initial_state), target=tuple(goal_state))
        # Devolver el siguiente mejor movimiento
        return list(shortest_path[1]) if len(shortest_path) > 1 else None
    except nx.NetworkXNoPath:
        return None