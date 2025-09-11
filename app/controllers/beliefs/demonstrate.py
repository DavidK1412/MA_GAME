"""
Demonstrate belief controller for demonstrating moves to players.
"""

from typing import Any, Dict, List
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
            # Obtener el número de intentos actuales
            tries_count = get_tries_count(game_id, self.db_client)
            
            # En los primeros 2 movimientos, no activar Demonstrate
            if tries_count <= 2:
                # Establecer valores que resulten en una puntuación muy baja
                new_values = {
                    "IP": tries_count,
                    "TPM": 0,  # Tiempo muy bajo para reducir puntuación
                    "A": 10    # Número alto de aserciones para reducir puntuación
                }
                self.values = new_values
                self.log_operation("values_updated_early_moves", {
                    "game_id": game_id, 
                    "values": new_values,
                    "tries_count": tries_count,
                    "reason": "Primeros 2 movimientos - Demonstrate desactivado"
                })
                return True
            
            new_values = {
                "IP": tries_count,
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
                
                # Generate varied demonstration text
                text = self._generate_demonstration_text(movement_state, best_movement)
                
                # Return demonstration data with proper format
                return {
                    "type": "CORRECT",
                    "actions": {
                        "text": text,
                        "last_state": movement_state,
                        "best_next_state": best_movement
                    }
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
    
    def _generate_demonstration_text(self, last_state: List[int], best_next_state: List[int]) -> str:
        """Generate varied demonstration text with rules, jokes, and motivation."""
        import random
        
        # Analyze the movement to provide context
        movement_type = self._analyze_movement_type(last_state, best_next_state)
        
        # Different categories of messages
        rule_reminders = [
            "¡Perfecto! Recuerda: las ranas solo pueden moverse hacia adelante, una casilla o saltando sobre otra rana.",
            "¡Excelente! Las ranas no pueden retroceder, solo avanzar hacia su destino.",
            "¡Muy bien! Observa cómo la rana salta sobre otra: es la clave para ganar eficientemente.",
            "¡Correcto! Las ranas del equipo izquierdo van hacia la derecha, las del derecho hacia la izquierda."
        ]
        
        motivational_jokes = [
            "¡Qué salto tan elegante! 🐸 Las ranas están más coordinadas que un ballet.",
            "¡Perfecto! Esta rana tiene mejor estrategia que un ajedrecista profesional.",
            "¡Excelente movimiento! Las ranas están trabajando en equipo mejor que los humanos.",
            "¡Qué inteligente! Esta rana debería dar clases de estrategia.",
            "¡Increíble! Las ranas están más organizadas que el tráfico en hora pico.",
            "¡Perfecto! Esta rana tiene más visión estratégica que un general."
        ]
        
        explanations = [
            "Observa cómo este movimiento acerca a las ranas a sus posiciones finales.",
            "Este es el camino más eficiente hacia la victoria. ¡Sigue así!",
            "Mira cómo cada movimiento cuenta para llegar al objetivo final.",
            "Este paso te acerca un poco más a completar el nivel.",
            "¡Estrategia perfecta! Cada movimiento tiene un propósito.",
            "Observa la secuencia: cada rana se mueve hacia su destino."
        ]
        
        encouragement = [
            "¡Sigue así! Estás dominando el juego de las ranas.",
            "¡Excelente! Tu comprensión del juego mejora con cada movimiento.",
            "¡Perfecto! Estás desarrollando una gran estrategia.",
            "¡Muy bien! Las ranas están orgullosas de tu progreso.",
            "¡Increíble! Estás convirtiéndote en un maestro del juego.",
            "¡Fantástico! Tu intuición para el juego es impresionante."
        ]
        
        # Select message type based on movement analysis and randomness
        message_types = []
        
        # Always include some explanation
        message_types.append(("explanations", explanations))
        
        # Add rule reminder 30% of the time
        if random.random() < 0.3:
            message_types.append(("rule_reminders", rule_reminders))
        
        # Add motivational joke 40% of the time
        if random.random() < 0.4:
            message_types.append(("motivational_jokes", motivational_jokes))
        
        # Add encouragement 50% of the time
        if random.random() < 0.5:
            message_types.append(("encouragement", encouragement))
        
        # Combine selected messages
        selected_messages = []
        for msg_type, messages in message_types:
            selected_messages.append(random.choice(messages))
        
        # Join messages with appropriate connectors
        if len(selected_messages) == 1:
            return selected_messages[0]
        elif len(selected_messages) == 2:
            return f"{selected_messages[0]} {selected_messages[1]}"
        else:
            return f"{selected_messages[0]} {selected_messages[1]} {selected_messages[2]}"
    
    def _analyze_movement_type(self, last_state: List[int], best_next_state: List[int]) -> str:
        """Analyze the type of movement being demonstrated."""
        # Find the position that changed
        for i, (old, new) in enumerate(zip(last_state, best_next_state)):
            if old != new:
                # Check if it's a jump (moved 2 positions)
                if abs(i - best_next_state.index(old)) == 2:
                    return "jump"
                else:
                    return "single_move"
        return "unknown"
    
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