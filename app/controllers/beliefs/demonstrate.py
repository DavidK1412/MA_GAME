"""
Demonstrate belief controller for demonstrating moves to players.
"""

from typing import Any, Dict
from controllers.base import BeliefController
from domain.models.response import SpeechResponse, Response, ResponseType
from utils.incentive_scripts import get_tries_count, get_average_time_between_state_change, get_number_of_assertions
from utils.graph_utils import best_next_move


class DemonstrateController(BeliefController):
    """
    Demonstrate belief controller that demonstrates moves based on player performance.
    """
    
    def __init__(self, db_client, name: str = "Demonstrate"):
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
                "IP": get_tries_count(game_id, self.db_client),
                "TPM": get_average_time_between_state_change(game_id, self.db_client),
                "A": get_number_of_assertions(game_id, self.db_client)
            }
            self.values = new_values
            self.log_operation("values_updated", {"game_id": game_id, "values": new_values})
            return True
            
        except Exception as e:
            self.log_error("values_update", e, {"game_id": game_id})
            return False
    
    def action(self, game_id: str) -> Response:
        """
        Provide demonstrate action based on belief evaluation.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Response with demonstration data
        """
        try:
            # Get current active attempt
            attempt = self._get_active_attempt(game_id)
            if not attempt:
                raise ValueError(f"No active attempt found for game {game_id}")
            
            attempt_id = attempt['id']
            difficulty_id = int(attempt['difficulty_id'])
            
            # Mark last movement as interrupted
            self._mark_last_movement_interrupted(attempt_id)
            
            # Get the previous movement
            last_movement = self._get_previous_movement(attempt_id)
            if not last_movement:
                return SpeechResponse.create_error("No se encontró movimiento anterior")
            
            # Get difficulty configuration
            difficulty_config = self._get_difficulty_config(difficulty_id)
            if not difficulty_config:
                return SpeechResponse.create_error("Configuración de dificultad no encontrada")
            
            # Parse movement and get best next move
            movement_state = [int(x) for x in last_movement['movement'].split(",")]
            
            try:
                best_movement = best_next_move(movement_state, difficulty_config['final_state'])
                
                if best_movement is None:
                    # Si no se puede encontrar el mejor movimiento, devolver un mensaje de ayuda
                    return SpeechResponse.create_rule_reminder(
                        "No se pudo calcular el mejor movimiento en este momento. "
                        "Recuerda: las ranas solo pueden moverse hacia adelante, "
                        "una casilla o saltando sobre otra rana."
                    )
                
                # Return demonstration data
                return {
                    "type": "CORRECT",
                    "last_state": movement_state,
                    "best_next_state": best_movement
                }
                
            except Exception as e:
                self.log_error("best_next_move_calculation", e, {
                    "game_id": game_id,
                    "movement_state": movement_state,
                    "final_state": difficulty_config['final_state']
                })
                return SpeechResponse.create_rule_reminder(
                    "Hubo un problema al calcular la demostración. "
                    "Recuerda las reglas básicas del juego."
                )
            
        except Exception as e:
            self.log_error("demonstrate_action", e, {"game_id": game_id})
            return SpeechResponse.create_error("Error al generar la demostración")
    
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
    
    def _get_previous_movement(self, attempt_id: str):
        """Get the previous movement (second to last)."""
        query = """
            SELECT * FROM movements 
            WHERE attempt_id = %s 
            AND step = (
                SELECT MAX(step) FROM movements WHERE attempt_id = %s
            ) - 1
        """
        result = self.safe_fetch_results(query, (attempt_id, attempt_id))
        return result[0] if result else None
    
    def _get_difficulty_config(self, difficulty_id: int):
        """Get difficulty configuration."""
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
        return difficulty_configs.get(difficulty_id)