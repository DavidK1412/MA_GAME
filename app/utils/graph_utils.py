"""
Enhanced graph utilities for the Frog Game with better error handling and validation.
"""

from collections import deque, defaultdict
import networkx as nx
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GraphUtilsError(Exception):
    """Custom exception for graph utilities errors."""
    pass


def validate_game_state(state: List[int], expected_length: int) -> None:
    """
    Validate that a game state is valid.
    
    Args:
        state: The game state to validate
        expected_length: Expected length of the state
        
    Raises:
        GraphUtilsError: If state is invalid
    """
    if not isinstance(state, list):
        raise GraphUtilsError("State must be a list")
    
    if len(state) != expected_length:
        raise GraphUtilsError(f"State must have {expected_length} positions, got {len(state)}")
    
    if 0 not in state:
        raise GraphUtilsError("State must contain exactly one empty position (0)")
    
    if state.count(0) != 1:
        raise GraphUtilsError("State must contain exactly one empty position (0)")
    
    # Validate all elements are integers
    if not all(isinstance(x, int) for x in state):
        raise GraphUtilsError("All state elements must be integers")


def is_left_frog(frog: int, total_left: int) -> bool:
    """Check if a frog is a left frog."""
    return 1 <= frog <= total_left


def is_right_frog(frog: int, total_left: int, total_right: int) -> bool:
    """Check if a frog is a right frog."""
    return total_left < frog <= total_left + total_right


def is_valid_move(state: List[int], i: int, j: int, total_left: int, total_right: int) -> bool:
    """
    Check if a move from position i to j is valid.
    
    Args:
        state: Current game state
        i: Source position
        j: Target position
        total_left: Number of left frogs
        total_right: Number of right frogs
        
    Returns:
        True if move is valid, False otherwise
    """
    try:
        if not (0 <= i < len(state) and 0 <= j < len(state)):
            return False
            
        frog = state[i]
        if frog == 0:
            return False

        direction = j - i
        if abs(direction) not in [1, 2]:
            return False
            
        if state[j] != 0:
            return False

        # Left frog moving right
        if direction > 0 and is_left_frog(frog, total_left):
            if abs(direction) == 2:  # Jump
                # Para saltar, debe haber una rana del equipo contrario en la posición intermedia
                middle_pos = i + 1
                if middle_pos < len(state) and not is_left_frog(state[middle_pos], total_left) and state[middle_pos] != 0:
                    return True  # Can jump over opposite team
                else:
                    return False  # Can't jump over empty space or own team
            return True

        # Right frog moving left
        if direction < 0 and is_right_frog(frog, total_left, total_right):
            if abs(direction) == 2:  # Jump
                # Para saltar, debe haber una rana del equipo contrario en la posición intermedia
                middle_pos = i - 1
                if middle_pos >= 0 and not is_right_frog(state[middle_pos], total_left, total_right) and state[middle_pos] != 0:
                    return True  # Can jump over opposite team
                else:
                    return False  # Can't jump over empty space or own team
            return True

        return False
        
    except Exception as e:
        logger.error(f"Error validating move: {e}")
        return False


def generate_neighbors(state: List[int], total_left: int, total_right: int) -> List[List[int]]:
    """
    Generate all valid neighbor states from current state.
    
    Args:
        state: Current game state
        total_left: Number of left frogs
        total_right: Number of right frogs
        
    Returns:
        List of valid neighbor states
    """
    try:
        neighbors = []
        empty_index = state.index(0)

        for offset in [-2, -1, 1, 2]:
            i = empty_index + offset
            if 0 <= i < len(state):
                if is_valid_move(state, i, empty_index, total_left, total_right):
                    new_state = state[:]
                    new_state[empty_index], new_state[i] = new_state[i], new_state[empty_index]
                    neighbors.append(new_state)
                    
        return neighbors
        
    except Exception as e:
        logger.error(f"Error generating neighbors: {e}")
        return []


def shortest_path_length(total_left: int, total_right: int, start_state: List[int], 
                        goal_state: List[int], max_depth: int = 100) -> Optional[int]:
    """
    Find the shortest path length from start_state to goal_state.
    
    Args:
        total_left: Number of left frogs
        total_right: Number of right frogs
        start_state: Starting game state
        goal_state: Target game state
        max_depth: Maximum search depth
        
    Returns:
        Shortest path length or None if no path found
    """
    try:
        # Validate states
        expected_length = total_left + total_right + 1
        validate_game_state(start_state, expected_length)
        validate_game_state(goal_state, expected_length)
        
        def generate_neighbors_wrapper(state):
            return generate_neighbors(state, total_left, total_right)

        visited = set()
        queue = deque([(start_state, 1)])  # state and depth

        while queue:
            current, depth = queue.popleft()
            current_tuple = tuple(current)

            if current == goal_state:
                return depth

            if current_tuple in visited or depth > max_depth:
                continue

            visited.add(current_tuple)

            for neighbor in generate_neighbors_wrapper(current):
                queue.append((neighbor, depth + 1))

        return None  # No path found
        
    except Exception as e:
        logger.error(f"Error in shortest_path_length: {e}")
        return None


def possible_moves(total_left: int, total_right: int, initial_state: List[int]) -> List[List[int]]:
    """
    Get all possible moves from initial state.
    
    Args:
        total_left: Number of left frogs
        total_right: Number of right frogs
        initial_state: Current game state
        
    Returns:
        List of possible next states
    """
    try:
        # Validate state
        expected_length = total_left + total_right + 1
        validate_game_state(initial_state, expected_length)
        
        return generate_neighbors(initial_state, total_left, total_right)
        
    except Exception as e:
        logger.error(f"Error in possible_moves: {e}")
        return []


def best_next_move(initial_state: List[int], goal_state: List[int]) -> Optional[List[int]]:
    """
    Find the best next move towards the goal state.
    
    Args:
        initial_state: Current game state
        goal_state: Target game state
        
    Returns:
        Best next state or None if no valid move
    """
    try:
        # Validate states
        if len(initial_state) != len(goal_state):
            logger.error("Initial and goal states must have same length")
            return None
            
        expected_length = len(initial_state)
        validate_game_state(initial_state, expected_length)
        validate_game_state(goal_state, expected_length)
        
        # Calculate total frogs
        total_frogs = expected_length - 1
        total_left = total_frogs // 2
        total_right = total_frogs - total_left
        
        def generate_neighbors_wrapper(state):
            return generate_neighbors(state, total_left, total_right)

        def build_graph(start_state: List[int]) -> dict:
            """Build graph from start state."""
            graph = defaultdict(list)
            queue = [start_state]
            visited = set()
            max_iterations = 1000  # Prevent infinite loops
            iteration_count = 0

            while queue and iteration_count < max_iterations:
                current_state = queue.pop(0)
                current_tuple = tuple(current_state)
                
                if current_tuple in visited:
                    continue
                    
                visited.add(current_tuple)
                iteration_count += 1

                neighbors = generate_neighbors_wrapper(current_state)
                graph[current_tuple] = [tuple(neighbor) for neighbor in neighbors]

                for neighbor in neighbors:
                    if tuple(neighbor) not in visited:
                        queue.append(neighbor)
                        
            if iteration_count >= max_iterations:
                logger.warning("Graph building stopped due to max iterations")
                
            return graph

        # Build graph from initial state
        graph_dict = build_graph(initial_state)
        
        if not graph_dict:
            logger.warning("No graph could be built")
            # Fallback: elegir mejor vecino por heurística
            neighbors = generate_neighbors_wrapper(initial_state)
            if not neighbors:
                logger.info("No neighbors available from current state")
                return None
            best = min(neighbors, key=lambda s: sum(1 for a, b in zip(s, goal_state) if a != b))
            return best
            
        # Create NetworkX graph
        G = nx.DiGraph()
        # Asegurar nodos aún si no tienen aristas salientes
        G.add_nodes_from(graph_dict.keys())
        for state, neighbors in graph_dict.items():
            for neighbor in neighbors:
                G.add_edge(state, neighbor)
        # Asegurar presencia explícita de source y target
        G.add_node(tuple(initial_state))
        G.add_node(tuple(goal_state))

        # Find shortest path
        try:
            shortest_path = nx.shortest_path(
                G, 
                source=tuple(initial_state), 
                target=tuple(goal_state)
            )
            
            if len(shortest_path) > 1:
                return list(shortest_path[1])
            else:
                return None
                
        except nx.NetworkXNoPath:
            logger.info("No path found to goal state")
            # Fallback: elegir mejor vecino por heurística
            neighbors = generate_neighbors_wrapper(initial_state)
            if not neighbors:
                logger.warning(f"No neighbors available from current state: {initial_state}")
                return None
            
            # Log para debug
            logger.debug(f"Using heuristic fallback with {len(neighbors)} neighbors")
            best = min(neighbors, key=lambda s: sum(1 for a, b in zip(s, goal_state) if a != b))
            logger.debug(f"Selected best neighbor: {best}")
            return best
        except Exception as e:
            logger.error(f"Error finding shortest path: {e}")
            # Fallback: elegir mejor vecino por heurística
            neighbors = generate_neighbors_wrapper(initial_state)
            if not neighbors:
                logger.warning(f"No neighbors available from current state: {initial_state}")
                return None
            
            # Log para debug
            logger.debug(f"Using error fallback with {len(neighbors)} neighbors")
            best = min(neighbors, key=lambda s: sum(1 for a, b in zip(s, goal_state) if a != b))
            logger.debug(f"Selected best neighbor: {best}")
            return best
            
    except Exception as e:
        logger.error(f"Error in best_next_move: {e}")
        return None


def calculate_game_complexity(state: List[int], total_left: int, total_right: int) -> float:
    """
    Calculate game complexity based on current state.
    
    Args:
        state: Current game state
        total_left: Number of left frogs
        total_right: Number of right frogs
        
    Returns:
        Complexity score (0-1)
    """
    try:
        if not state:
            return 0.0
            
        # Count possible moves
        possible_moves_count = len(possible_moves(total_left, total_right, state))
        
        # Normalize by maximum possible moves (usually 4)
        max_possible_moves = 4
        complexity = min(possible_moves_count / max_possible_moves, 1.0)
        
        return complexity
        
    except Exception as e:
        logger.error(f"Error calculating game complexity: {e}")
        return 0.0


def is_game_winnable(initial_state: List[int], goal_state: List[int]) -> bool:
    """
    Check if the game is winnable from current state.
    
    Args:
        initial_state: Current game state
        goal_state: Target game state
        
    Returns:
        True if game is winnable, False otherwise
    """
    try:
        if len(initial_state) != len(goal_state):
            return False
            
        expected_length = len(initial_state)
        total_frogs = expected_length - 1
        total_left = total_frogs // 2
        total_right = total_frogs - total_left
        
        # Check if there's a path to goal
        path_length = shortest_path_length(total_left, total_right, initial_state, goal_state)
        return path_length is not None
        
    except Exception as e:
        logger.error(f"Error checking if game is winnable: {e}")
        return False