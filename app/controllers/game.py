"""
Game controller for managing game logic and state.
"""

import uuid
from typing import Optional, Dict, Any, List
from controllers.base import BaseController
from domain.models.game import GameType, GameState, GameAttempt
from domain.models.movement import MovementRequestType, Movement, MovementType
from domain.models.response import Response, ResponseType, GameResponse, SpeechResponse
from core.exceptions import GameNotFoundError, InvalidMovementError, GameCompletedError
from utils.graph_utils import best_next_move


class GameController(BaseController):
    """Controller for managing game operations and state."""
    
    def __init__(self, db_client):
        super().__init__(db_client, "GameController")
        self._difficulty_configs = {
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

    def create_game(self, params: GameType) -> bool:
        """Create a new game."""
        try:
            query = "INSERT INTO game (id) VALUES (%s)"
            self.safe_execute_query(query, (params.game_id,))
            self.log_operation("game_created", {"game_id": params.game_id})
            return True
        except Exception as e:
            self.log_error("game_creation", e, {"game_id": params.game_id})
            raise

    def get_game_by_id(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get game by ID."""
        query = "SELECT * FROM game WHERE id = %s AND is_finished IS FALSE"
        result = self.safe_fetch_results(query, (game_id,))
        return result[0] if result else None

    def start_attempt(self, game_id: str, movement: MovementRequestType) -> Optional[str]:
        """Start a new game attempt."""
        try:
            # Check if there's already an active attempt
            if self._has_active_attempt(game_id):
                self.log_operation("attempt_already_active", {"game_id": game_id})
                return None
            
            attempt_id = str(uuid.uuid4())
            difficulty_id = self._calculate_difficulty(movement)
            
            query = "INSERT INTO game_attempts(id, game_id, difficulty_id) VALUES (%s, %s, %s)"
            self.safe_execute_query(query, (attempt_id, game_id, difficulty_id))
            
            self.log_operation("attempt_started", {
                "attempt_id": attempt_id,
                "game_id": game_id,
                "difficulty_id": difficulty_id
            })
            return attempt_id
            
        except Exception as e:
            self.log_error("attempt_start", e, {"game_id": game_id})
            raise

    def _start_attempt_with_difficulty(self, game_id: str, difficulty_id: int) -> Optional[str]:
        """Start a new game attempt with an explicit difficulty."""
        try:
            # Debe no existir intento activo
            if self._has_active_attempt(game_id):
                self.log_operation("attempt_already_active", {"game_id": game_id})
                return None

            attempt_id = str(uuid.uuid4())
            query = "INSERT INTO game_attempts(id, game_id, difficulty_id) VALUES (%s, %s, %s)"
            self.safe_execute_query(query, (attempt_id, game_id, difficulty_id))

            self.log_operation("attempt_started", {
                "attempt_id": attempt_id,
                "game_id": game_id,
                "difficulty_id": difficulty_id
            })
            return attempt_id
        except Exception as e:
            self.log_error("attempt_start_with_difficulty", e, {"game_id": game_id, "difficulty_id": difficulty_id})
            raise

    def move(self, game_id: str, movement: MovementRequestType, config: Dict):
        """Process a game move."""
        try:
            attempt = self._get_active_attempt(game_id)
            if not attempt:
                # No hay intento activo: crear uno automáticamente con el primer movimiento
                attempt_id = self.start_attempt(game_id, movement)
                if not attempt_id:
                    raise GameNotFoundError(f"No active attempt found for game {game_id}")
                # Reconstruimos el objeto mínimo necesario para continuar
                attempt = {
                    'id': attempt_id,
                    'difficulty_id': self._calculate_difficulty(movement)
                }
            
            current_step = self._get_current_step(attempt['id'])
            
            # Si need_correct es True, solo guardar el movimiento sin procesar lógica de juego
            if movement.need_correct:
                self._save_movement(attempt['id'], movement, current_step + 1)
                self.log_operation("movement_saved_only", {
                    "game_id": game_id,
                    "attempt_id": attempt['id'],
                    "step": current_step + 1,
                    "need_correct": True
                })
                return "movement_saved"
            
            difficulty_config = self._difficulty_configs[attempt['difficulty_id']]
            
            # Validate and process the movement
            if self._is_best_move(movement, attempt, current_step, difficulty_config):
                self._save_correct_movement(attempt['id'], movement, current_step)
                raise GameCompletedError("Best movement")
            
            if self._is_final_move(movement, difficulty_config, current_step):
                self._save_correct_movement(attempt['id'], movement, current_step)
                self._complete_attempt(attempt['id'])
                # Subir de nivel si es posible
                try:
                    max_level = max(self._difficulty_configs.keys())
                    current_level = int(attempt['difficulty_id'])
                    if current_level < max_level:
                        new_level = current_level + 1
                        new_attempt_id = self._start_attempt_with_difficulty(game_id, new_level)
                        self.log_operation("level_up", {
                            "game_id": game_id,
                            "from": current_level,
                            "to": new_level,
                            "new_attempt_id": new_attempt_id
                        })
                        # Devolver DTO de cambio de dificultad
                        return GameResponse.difficulty_changed(
                            text="¡Nivel aumentado!",
                            level_change=1
                        )
                except Exception as e:
                    self.log_error("level_up_failed", e, {"game_id": game_id, "attempt_id": attempt['id']})
                # Si no se pudo subir nivel, finalizar normalmente
                raise GameCompletedError("Final movement")
            
            # Save regular movement
            self._save_movement(attempt['id'], movement, current_step + 1)
            
            if current_step == 0:
                raise GameCompletedError("First move")
            
            return True
            
        except Exception as e:
            self.log_error("move_processing", e, {"game_id": game_id})
            raise

    def miss(self, game_id: str) -> int:
        """Record a missed move."""
        try:
            attempt = self._get_active_attempt(game_id)
            if not attempt:
                raise GameNotFoundError(f"No active attempt found for game {game_id}")
            
            attempt_id = attempt['id']
            counter = self._get_miss_counter(attempt_id)
            
            if counter is None:
                # Create new miss counter
                counter = 1
                self._create_miss_counter(attempt_id, counter)
            else:
                # Update existing counter
                counter += 1
                self._update_miss_counter(attempt_id, counter)
            
            self.log_operation("miss_recorded", {
                "game_id": game_id,
                "attempt_id": attempt_id,
                "miss_count": counter
            })
            
            return counter
            
        except Exception as e:
            self.log_error("miss_recording", e, {"game_id": game_id})
            raise

    def get_best_next(self, game_id: str) -> Response:
        """Get the best next move for a game."""
        try:
            attempt = self._get_active_attempt(game_id)
            if not attempt:
                raise GameNotFoundError(f"No active attempt found for game {game_id}")
            
            last_movement = self._get_last_movement(attempt['id'])
            if not last_movement:
                raise InvalidMovementError("No previous movement found")
            
            difficulty_config = self._difficulty_configs[attempt['difficulty_id']]
            best_movement = best_next_move(last_movement, difficulty_config['final_state'])
            
            return Response(
                type=ResponseType.BEST_NEXT,
                actions={
                    "text": "Este es el movimiento correcto",
                    "best_next": best_movement
                }
            )
            
        except Exception as e:
            self.log_error("best_next_calculation", e, {"game_id": game_id})
            raise

    def _has_active_attempt(self, game_id: str) -> bool:
        """Check if game has an active attempt."""
        query = "SELECT COUNT(*) as count FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
        result = self.safe_fetch_results(query, (game_id,))
        return result[0]['count'] > 0 if result else False

    def _calculate_difficulty(self, movement: MovementRequestType) -> int:
        """Calculate difficulty based on movement size."""
        difficulties = {7: 1, 9: 2, 11: 3}
        return difficulties.get(len(movement.movement), 1)

    def _get_active_attempt(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get active attempt for a game."""
        query = "SELECT * FROM game_attempts WHERE game_id = %s AND is_active IS TRUE"
        result = self.safe_fetch_results(query, (game_id,))
        return result[0] if result else None

    def _get_current_step(self, attempt_id: str) -> int:
        """Get current step for an attempt."""
        query = "SELECT MAX(step) FROM movements WHERE attempt_id = %s"
        result = self.safe_fetch_results(query, (attempt_id,))
        return result[0]['max'] if result and result[0]['max'] else 0

    def get_tries_count(self, game_id: str) -> int:
        """Public helper to get current tries (steps) for the active attempt of a game."""
        try:
            attempt = self._get_active_attempt(game_id)
            if not attempt:
                return 0
            return self._get_current_step(attempt['id'])
        except Exception:
            return 0

    def _is_best_move(self, movement: MovementRequestType, attempt: Dict, current_step: int, difficulty_config: Dict) -> bool:
        """Check if movement is the best possible move."""
        if current_step < 1:
            return False
        
        last_movement = self._get_last_movement(attempt['id'])
        if not last_movement:
            return False
        
        best_movement = best_next_move(last_movement, difficulty_config['final_state'])
        return best_movement == movement.movement

    def _is_final_move(self, movement: MovementRequestType, difficulty_config: Dict, current_step: int) -> bool:
        """Check if movement is the final winning move."""
        return movement.movement == difficulty_config['final_state'] and current_step > 1

    def _save_correct_movement(self, attempt_id: str, movement: MovementRequestType, step: int) -> None:
        """Save a correct movement."""
        movement_str = self._format_movement_for_db(movement.movement)
        query = "INSERT INTO movements (id, attempt_id, step, movement, is_correct) VALUES (%s, %s, %s, %s, %s)"
        self.safe_execute_query(query, (str(uuid.uuid4()), attempt_id, step, movement_str, True))

    def _save_movement(self, attempt_id: str, movement: MovementRequestType, step: int) -> None:
        """Save a regular movement."""
        movement_str = self._format_movement_for_db(movement.movement)
        query = "INSERT INTO movements (id, attempt_id, step, movement) VALUES (%s, %s, %s, %s)"
        self.safe_execute_query(query, (str(uuid.uuid4()), attempt_id, step, movement_str))

    def _format_movement_for_db(self, movement: List[int]) -> str:
        """Format movement list for database storage."""
        return ','.join(str(item) for item in movement)

    def _get_last_movement(self, attempt_id: str) -> Optional[List[int]]:
        """Get the last movement for an attempt."""
        query = "SELECT movement FROM movements WHERE attempt_id = %s ORDER BY step DESC LIMIT 1"
        result = self.safe_fetch_results(query, (attempt_id,))
        if not result:
            return None
        
        movement_str = result[0]['movement']
        return [int(x) for x in movement_str.split(",")]

    def _complete_attempt(self, attempt_id: str) -> None:
        """Mark attempt as completed."""
        query = "UPDATE game_attempts SET is_active = FALSE WHERE id = %s"
        self.safe_execute_query(query, (attempt_id,))

    def _get_miss_counter(self, attempt_id: str) -> Optional[int]:
        """Get the current miss counter for an attempt."""
        query = "SELECT count FROM movements_misses WHERE game_attempt_id = %s"
        result = self.safe_fetch_results(query, (attempt_id,))
        return result[0]['count'] if result else None

    def _create_miss_counter(self, attempt_id: str, count: int) -> None:
        """Create a new miss counter."""
        query = "INSERT INTO movements_misses (id, game_attempt_id, count) VALUES (%s, %s, %s)"
        self.safe_execute_query(query, (str(uuid.uuid4()), attempt_id, count))

    def _update_miss_counter(self, attempt_id: str, count: int) -> None:
        """Update an existing miss counter."""
        query = "UPDATE movements_misses SET count = %s WHERE game_attempt_id = %s"
        self.safe_execute_query(query, (count, attempt_id))
