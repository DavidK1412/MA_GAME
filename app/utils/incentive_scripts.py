"""
Enhanced incentive scripts for calculating player metrics with better error handling.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
from .graph_utils import possible_moves, shortest_path_length, calculate_game_complexity, is_game_winnable
from time import time

logger = logging.getLogger(__name__)


class IncentiveScriptsError(Exception):
    """Custom exception for incentive scripts errors."""
    pass
_METRICS_CACHE: Dict[str, Dict[str, Any]] = {}
_METRICS_TTL_SECONDS: float = 2.0

def _cache_get(game_id: str) -> Optional[Dict[str, Any]]:
    item = _METRICS_CACHE.get(game_id)
    if not item:
        return None
    if time() - item.get("ts", 0) > _METRICS_TTL_SECONDS:
        _METRICS_CACHE.pop(game_id, None)
        return None
    return item.get("data")

def _cache_set(game_id: str, data: Dict[str, Any]) -> None:
    _METRICS_CACHE[game_id] = {"ts": time(), "data": data}



def get_actual_attempt_id(game_id: str, db_client) -> Optional[str]:
    """
    Get the current active attempt ID for a game.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Attempt ID or None if not found
    """
    try:
        query = "SELECT id FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
        params = (game_id,)
        result = db_client.fetch_results(query, params)
        
        if not result:
            logger.warning(f"No active attempt found for game {game_id}")
            return None
            
        return result[0]['id']
        
    except Exception as e:
        logger.error(f"Error getting actual attempt ID: {e}")
        return None


def get_average_time_between_state_change(game_id: str, db_client) -> float:
    """
    Calculate average time between state changes in a game attempt.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Average time in seconds
    """
    try:
        game_attempt_id = get_actual_attempt_id(game_id, db_client)
        if not game_attempt_id:
            return 0.0
            
        query = """
            SELECT movement_time 
            FROM movements 
            WHERE attempt_id = %s AND interuption IS FALSE 
            ORDER BY movement_time ASC
        """
        params = (game_attempt_id,)
        result = db_client.fetch_results(query, params)
        
        if len(result) < 2:
            return 0.0
            
        # Calculate time differences
        total_time_diff = timedelta()
        for i in range(1, len(result)):
            try:
                time1 = result[i-1]['movement_time']
                time2 = result[i]['movement_time']
                
                # Normalizar a datetime
                if isinstance(time1, str):
                    time1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
                if isinstance(time2, str):
                    time2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
                # Si vienen como datetime.time, convertir a datetime de hoy
                if hasattr(time1, 'hour') and not hasattr(time1, 'year'):
                    time1 = datetime.combine(datetime.today().date(), time1)
                if hasattr(time2, 'hour') and not hasattr(time2, 'year'):
                    time2 = datetime.combine(datetime.today().date(), time2)
                    
                time_diff = time2 - time1
                total_time_diff += time_diff
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing time at index {i}: {e}")
                continue
        
        if total_time_diff == timedelta():
            return 0.0
            
        avg_time_diff = total_time_diff / (len(result) - 1)
        return avg_time_diff.total_seconds()
        
    except Exception as e:
        logger.error(f"Error calculating average time: {e}")
        return 0.0


def get_repeated_states_count(game_id: str, db_client) -> int:
    """
    Count repeated states in a game attempt.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Number of repeated states
    """
    try:
        game_attempt_id = get_actual_attempt_id(game_id, db_client)
        if not game_attempt_id:
            return 0
            
        query = "SELECT movement FROM movements WHERE attempt_id = %s ORDER BY step ASC"
        params = (game_attempt_id,)
        result = db_client.fetch_results(query, params)
        
        if not result:
            return 0
            
        states = []
        repeated_states = 0
        
        for movement in result:
            movement_str = movement['movement']
            if movement_str in states:
                repeated_states += 1
            else:
                states.append(movement_str)
                
        logger.debug(f'Repeated states count: {repeated_states}')
        return repeated_states
        
    except Exception as e:
        logger.error(f"Error counting repeated states: {e}")
        return 0


def get_misses_count(game_id: str, db_client) -> int:
    """
    Get the count of missed moves for a game attempt.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Number of misses
    """
    try:
        game_attempt_id = get_actual_attempt_id(game_id, db_client)
        if not game_attempt_id:
            return 0
            
        query = "SELECT count FROM movements_misses WHERE game_attempt_id = %s"
        params = (game_attempt_id,)
        result = db_client.fetch_results(query, params)
        
        if not result or not result[0]['count']:
            return 0
            
        misses = result[0]['count']
        logger.debug(f'Misses count: {misses}')
        return misses
        
    except Exception as e:
        logger.error(f"Error getting misses count: {e}")
        return 0


def get_enhanced_buclicity(game_id: str, db_client) -> float:
    """
    Enhanced buclicity calculation for CIL children - measures learning patterns and persistence.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Enhanced buclicity value (0-1, normalized)
    """
    try:
        game_attempt_id = get_actual_attempt_id(game_id, db_client)
        if not game_attempt_id:
            return 0.0
            
        # Get all movements for pattern analysis
        query = "SELECT step, movement FROM movements WHERE attempt_id = %s ORDER BY step ASC"
        params = (game_attempt_id,)
        result = db_client.fetch_results(query, params)
        
        if len(result) < 3:  # Need at least 3 movements for meaningful analysis
            return 0.0
            
        movements = [(r['step'], r['movement']) for r in result]
        total_movements = len(movements)
        
        # Calculate pattern repetition score (adapted for CIL children)
        pattern_scores = []
        window_sizes = [2, 3]  # Check for 2-step and 3-step patterns
        
        for window_size in window_sizes:
            if total_movements < window_size:
                continue
                
            pattern_count = 0
            for i in range(window_size, total_movements):
                current_pattern = [movements[j][1] for j in range(i-window_size, i)]
                
                # Count occurrences of this pattern
                occurrences = 0
                for j in range(len(movements) - window_size + 1):
                    pattern = [movements[k][1] for k in range(j, j+window_size)]
                    if pattern == current_pattern:
                        occurrences += 1
                
                if occurrences > 1:
                    # Weight recent patterns more heavily for CIL children
                    recency_weight = (i - window_size + 1) / total_movements
                    pattern_count += (occurrences - 1) * recency_weight
            
            if total_movements > window_size:
                pattern_scores.append(pattern_count / (total_movements - window_size))
        
        # Calculate immediate repetition (CIL children often repeat immediately)
        immediate_repetitions = 0
        for i in range(1, total_movements):
            if movements[i][1] == movements[i-1][1]:
                immediate_repetitions += 1
        
        immediate_repetition_score = immediate_repetitions / max(1, total_movements - 1)
        
        # Combine pattern scores with immediate repetition
        if pattern_scores:
            avg_pattern_score = sum(pattern_scores) / len(pattern_scores)
            enhanced_buclicity = (avg_pattern_score * 0.7 + immediate_repetition_score * 0.3)
        else:
            enhanced_buclicity = immediate_repetition_score
        
        # Normalize to 0-1 range
        normalized_buclicity = min(1.0, enhanced_buclicity)
        
        # Update database
        try:
            update_query = "UPDATE game_attempts SET last_buclicity = %s WHERE id = %s"
            update_params = (normalized_buclicity, game_attempt_id)
            db_client.execute_query(update_query, update_params)
        except Exception as e:
            logger.warning(f"Could not update buclicity in database: {e}")
        
        logger.debug(f'Enhanced buclicity calculated: {normalized_buclicity}')
        return normalized_buclicity
        
    except Exception as e:
        logger.error(f"Error calculating enhanced buclicity: {e}")
        return 0.0

def get_buclicity(game_id: str, db_client) -> float:
    """Wrapper for backward compatibility."""
    return get_enhanced_buclicity(game_id, db_client)


def get_tries_count(game_id: str, db_client) -> int:
    """
    Get the number of tries (steps) for a game attempt.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Number of tries
    """
    try:
        game_attempt_id = get_actual_attempt_id(game_id, db_client)
        if not game_attempt_id:
            return 0
            
        query = "SELECT MAX(step) FROM movements WHERE attempt_id = %s"
        params = (game_attempt_id,)
        result = db_client.fetch_results(query, params)
        
        if not result or not result[0]['max']:
            return 0
            
        tries = result[0]['max']
        logger.debug(f'Tries count: {tries}')
        return tries
        
    except Exception as e:
        logger.error(f"Error getting tries count: {e}")
        return 0


def get_branch_factor(game_id: str, db_client) -> float:
    """
    Calculate branch factor (diversity of possible moves) for a game attempt.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Branch factor value
    """
    try:
        game_attempt_id = get_actual_attempt_id(game_id, db_client)
        if not game_attempt_id:
            return 1.0
            
        # Get difficulty configuration
        query = "SELECT difficulty_id FROM game_attempts WHERE id = %s"
        params = (game_attempt_id,)
        result = db_client.fetch_results(query, params)
        
        if not result:
            return 1.0
            
        difficulty_id = result[0]['difficulty_id']
        
        difficulty_configs = {
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
        
        if difficulty_id not in difficulty_configs:
            logger.warning(f"Unknown difficulty ID: {difficulty_id}")
            return 1.0
            
        difficulty = difficulty_configs[difficulty_id]
        blocks_per_team = difficulty['blocks_per_team']
        final_state = difficulty['final_state']
        
        # Get initial state
        query = "SELECT movement FROM movements WHERE attempt_id = %s ORDER BY step ASC LIMIT 1"
        params = (game_attempt_id,)
        result = db_client.fetch_results(query, params)
        
        if not result:
            return 1.0
            
        initial_state_str = result[0]['movement']
        try:
            initial_state = [int(x.strip()) for x in initial_state_str.split(",") if x.strip()]
        except (ValueError, AttributeError) as e:
            logger.error(f"Error parsing initial state: {e}")
            return 1.0
        
        # Calculate branch factor
        try:
            possible_moves_list = possible_moves(blocks_per_team, blocks_per_team, initial_state)
            P = len(possible_moves_list)
            
            if P == 0:
                return 1.0
                
            S = 0
            valid_moves = 0
            
            for move in possible_moves_list:
                try:
                    value = shortest_path_length(blocks_per_team, blocks_per_team, move, final_state)
                    if value is not None:
                        S += value
                        valid_moves += 1
                except Exception as e:
                    logger.warning(f"Error calculating path length for move: {e}")
                    continue
            
            if valid_moves == 0:
                return 1.0
                
            B = S / valid_moves
            logger.debug(f'Branch factor calculated: {B}')
            return B
            
        except Exception as e:
            logger.error(f"Error calculating branch factor: {e}")
            return 1.0
            
    except Exception as e:
        logger.error(f"Error in get_branch_factor: {e}")
        return 1.0


def get_number_of_assertions(game_id: str, db_client) -> int:
    """
    Get the number of correct moves for a game attempt.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Number of correct moves
    """
    try:
        game_attempt_id = get_actual_attempt_id(game_id, db_client)
        if not game_attempt_id:
            return 0
            
        query = "SELECT COUNT(*) as count FROM movements WHERE attempt_id = %s AND is_correct IS TRUE"
        params = (game_attempt_id,)
        result = db_client.fetch_results(query, params)
        
        if not result:
            return 0
            
        return result[0]['count']
        
    except Exception as e:
        logger.error(f"Error getting number of assertions: {e}")
        return 0


def get_game_progress(game_id: str, db_client) -> Dict[str, Any]:
    """
    Get comprehensive game progress metrics.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Dictionary with all game metrics
    """
    try:
        # Cache de métricas para evitar consultas repetidas en ventanas cortas
        cached = _cache_get(game_id)
        if cached is not None:
            return cached
        metrics = {
            'tries_count': get_tries_count(game_id, db_client),
            'misses_count': get_misses_count(game_id, db_client),
            'buclicity': get_buclicity(game_id, db_client),
            'branch_factor': get_branch_factor(game_id, db_client),
            'repeated_states': get_repeated_states_count(game_id, db_client),
            'average_time': get_average_time_between_state_change(game_id, db_client),
            'correct_moves': get_number_of_assertions(game_id, db_client)
        }
        _cache_set(game_id, metrics)
        logger.debug(f"Game progress metrics calculated: {metrics}")
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting game progress: {e}")
        return {
            'tries_count': 0,
            'misses_count': 0,
            'buclicity': 0.0,
            'branch_factor': 1.0,
            'repeated_states': 0,
            'average_time': 0.0,
            'correct_moves': 0
        }


def calculate_player_skill_level(game_id: str, db_client) -> float:
    """
    Calculate overall player skill level based on multiple metrics.
    
    Args:
        game_id: Game identifier
        db_client: Database client instance
        
    Returns:
        Skill level score (0-1)
    """
    try:
        metrics = get_game_progress(game_id, db_client)
        
        # Normalize and weight different metrics
        tries_score = max(0, 1 - (metrics['tries_count'] / 20))  # Lower tries = better
        misses_score = max(0, 1 - (metrics['misses_count'] / 10))  # Lower misses = better
        buclicity_score = max(0, 1 - (metrics['buclicity'] / 10))  # Lower buclicity = better
        branch_score = min(1, metrics['branch_factor'] / 5)  # Higher branch factor = better
        time_score = max(0, 1 - (metrics['average_time'] / 60))  # Lower time = better
        correct_score = min(1, metrics['correct_moves'] / 10)  # Higher correct moves = better
        
        # Weighted average
        weights = {
            'tries': 0.25,
            'misses': 0.20,
            'buclicity': 0.15,
            'branch': 0.20,
            'time': 0.10,
            'correct': 0.10
        }
        
        skill_level = (
            tries_score * weights['tries'] +
            misses_score * weights['misses'] +
            buclicity_score * weights['buclicity'] +
            branch_score * weights['branch'] +
            time_score * weights['time'] +
            correct_score * weights['correct']
        )
        
        logger.debug(f"Player skill level calculated: {skill_level}")
        return min(1.0, max(0.0, skill_level))
        
    except Exception as e:
        logger.error(f"Error calculating player skill level: {e}")
        return 0.5 