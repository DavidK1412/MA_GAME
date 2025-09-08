"""
Ask belief controller for asking questions to players.
"""

from typing import Any, Dict
from controllers.base import BeliefController
from domain.models.response import SpeechResponse, Response, ResponseType
from utils.incentive_scripts import get_buclicity, get_average_time_between_state_change


class AskController(BeliefController):
    """
    Ask belief controller that asks questions based on player performance.
    """
    
    def __init__(self, db_client, name: str = "Ask"):
        super().__init__(db_client, name)
    
    def update_values(self, game_id: str, config: Dict[str, Any]) -> bool:
        """
        Update belief values based on equation variables from config.
        
        Args:
            game_id: Game identifier
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            new_values = {
                "B": get_buclicity(game_id, self.db_client),
                "TP": get_average_time_between_state_change(game_id, self.db_client)
            }
            self.values = new_values
            self.log_operation("values_updated", {"game_id": game_id, "values": new_values})
            return True
            
        except Exception as e:
            self.log_error("values_update", e, {"game_id": game_id})
            return False
    
    def action(self, game_id: str) -> Response:
        """
        Provide ask action based on belief evaluation.
        
        Args:
            game_id: Game identifier
            
        Returns:
            SpeechResponse with question message
        """
        try:
            # Get current active attempt
            attempt = self._get_active_attempt(game_id)
            if not attempt:
                raise ValueError(f"No active attempt found for game {game_id}")
            
            attempt_id = attempt['id']
            
            # Mark last movement as interrupted
            self._mark_last_movement_interrupted(attempt_id)
            
            return SpeechResponse.create_question(
                "¿Necesitas ayuda en el siguiente movimiento?"
            )
            
        except Exception as e:
            self.log_error("ask_action", e, {"game_id": game_id})
            return SpeechResponse.create_question(
                "¿Necesitas ayuda?"
            )
    
    def _get_active_attempt(self, game_id: str):
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