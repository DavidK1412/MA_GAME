"""
Advice belief controller for providing guidance to players.
"""

import uuid
from typing import Optional, Dict, Any
from controllers.base import BeliefController
from domain.models.response import SpeechResponse, GameResponse, ResponseType
from core.exceptions import GameNotFoundError, InvalidMovementError
from utils.incentive_scripts import get_tries_count, get_branch_factor


class AdviceController(BeliefController):
    """Controller for providing advice to players based on their performance."""
    
    def __init__(self, db_client, name: str = "Advice"):
        super().__init__(db_client, name)

    def update_values(self, game_id: str, config: Dict[str, Any]) -> bool:
        """Update belief values for advice calculation using equation variables."""
        try:
            new_values = {
                "IP": get_tries_count(game_id, self.db_client),
                "R": get_branch_factor(game_id, self.db_client)
            }
            self.values = new_values
            self.log_operation("values_updated", {"game_id": game_id, "values": new_values})
            return True
        except Exception as e:
            self.log_error("values_update", e, {"game_id": game_id})
            return False
    
    def action(self, game_id: str) -> SpeechResponse | GameResponse:
        """Execute advice action for the player."""
        try:
            # Get current active attempt
            attempt = self._get_active_attempt(game_id)
            if not attempt:
                raise GameNotFoundError(f"No active attempt found for game {game_id}")
            
            attempt_id = attempt['id']
            difficulty_id = int(attempt['difficulty_id'])
            
            # Mark last movement as interrupted
            self._mark_last_movement_interrupted(attempt_id)
            
            # Handle minimum difficulty level
            if difficulty_id == 1:
                return self._create_encouragement_response()
            
            # Reduce difficulty and restart
            return self._reduce_difficulty_and_restart(game_id, attempt_id, difficulty_id)
            
        except Exception as e:
            self.log_error("advice_action", e, {"game_id": game_id})
            raise
    
    def _get_active_attempt(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get the current active attempt for a game."""
        query = """
            SELECT * FROM game_attempts 
            WHERE game_id = %s AND is_active IS TRUE
        """
        result = self.safe_fetch_results(query, (game_id,))
        return result[0] if result else None
    
    def _mark_last_movement_interrupted(self, attempt_id: str) -> None:
        """Mark the last movement as interrupted."""
        query = """
            UPDATE movements 
            SET interuption = TRUE 
            WHERE attempt_id = %s 
            AND step = (
                SELECT MAX(step) 
                FROM movements 
                WHERE attempt_id = %s
            )
        """
        self.safe_execute_query(query, (attempt_id, attempt_id))
        self.log_operation("movement_marked_interrupted", {"attempt_id": attempt_id})
    
    def _create_encouragement_response(self) -> SpeechResponse:
        """Create encouragement response for minimum difficulty."""
        return SpeechResponse.create_encouragement(
            "Tal vez necesitas algo más de práctica, ¡mucho ánimo!"
        )
    
    def _reduce_difficulty_and_restart(self, game_id: str, attempt_id: str, current_difficulty: int) -> GameResponse:
        """Reduce difficulty and restart the game attempt."""
        try:
            with self.db_client.transaction():
                # Deactivate current attempt
                self.safe_execute_query(
                    "UPDATE game_attempts SET is_active = FALSE WHERE id = %s",
                    (attempt_id,)
                )
                
                # Create new attempt with reduced difficulty
                new_attempt_id = str(uuid.uuid4())
                new_difficulty = max(1, current_difficulty - 1)
                
                self.safe_execute_query(
                    "INSERT INTO game_attempts (id, game_id, difficulty_id) VALUES (%s, %s, %s)",
                    (new_attempt_id, game_id, new_difficulty)
                )
                
                self.log_operation("difficulty_reduced", {
                    "game_id": game_id,
                    "old_difficulty": current_difficulty,
                    "new_difficulty": new_difficulty,
                    "new_attempt_id": new_attempt_id
                })
                
                return GameResponse.difficulty_changed(
                    "No te desanimes, vamos a intentarlo con un cubo menos",
                    -1
                )
                
        except Exception as e:
            self.log_error("difficulty_reduction", e, {
                "game_id": game_id,
                "attempt_id": attempt_id,
                "current_difficulty": current_difficulty
            })
            raise
