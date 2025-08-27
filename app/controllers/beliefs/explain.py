"""
Explain belief controller for providing explanations to players.
"""

from typing import Any, Dict
from app.controllers.base import BeliefController
from app.domain.models.response import SpeechResponse
from app.utils.incentive_scripts import get_game_progress, calculate_player_skill_level


class ExplainController(BeliefController):
    """
    Explain belief controller that provides explanations based on player performance.
    """
    
    def __init__(self, db_client, name: str = "Explain"):
        super().__init__(db_client, name)
    
    def update_values(self, game_id: str, config: Dict[str, Any]) -> bool:
        """
        Update belief values based on game metrics.
        
        Args:
            game_id: Game identifier
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get game progress metrics
            metrics = get_game_progress(game_id, self.db_client)
            
            # Calculate belief value based on player understanding
            # Higher belief value when player needs more explanation
            belief_value = 0.0
            
            # Factor 1: High tries count suggests confusion
            if metrics['tries_count'] > 15:
                belief_value += 0.4
            elif metrics['tries_count'] > 10:
                belief_value += 0.3
            elif metrics['tries_count'] > 5:
                belief_value += 0.2
            
            # Factor 2: High misses indicate rule misunderstanding
            if metrics['misses_count'] > 5:
                belief_value += 0.3
            elif metrics['misses_count'] > 2:
                belief_value += 0.2
            
            # Factor 3: High buclicity suggests getting stuck
            if metrics['buclicity'] > 5:
                belief_value += 0.2
            
            # Factor 4: Low skill level needs more explanation
            skill_level = calculate_player_skill_level(game_id, self.db_client)
            if skill_level < 0.3:
                belief_value += 0.3
            elif skill_level < 0.6:
                belief_value += 0.2
            
            # Cap belief value at 1.0
            belief_value = min(1.0, belief_value)
            
            # Store belief value in database
            query = """
                UPDATE game_attempts 
                SET explain_belief = %s 
                WHERE game_id = %s AND is_active = TRUE
            """
            params = (belief_value, game_id)
            
            return self.safe_execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error updating explain belief values: {e}")
            return False
    
    def action(self, game_id: str) -> SpeechResponse:
        """
        Provide explanation action based on belief evaluation.
        
        Args:
            game_id: Game identifier
            
        Returns:
            SpeechResponse with explanation message
        """
        try:
            # Get current belief value
            query = "SELECT explain_belief FROM game_attempts WHERE game_id = %s AND is_active = TRUE"
            params = (game_id,)
            result = self.db_client.fetch_results(query, params)
            
            if not result:
                return SpeechResponse(
                    message="No se pudo obtener información del juego para explicar.",
                    belief_value=0.0
                )
            
            belief_value = result[0].get('explain_belief', 0.0)
            
            # Generate explanation based on belief value
            if belief_value > 0.7:
                message = (
                    "Veo que estás teniendo dificultades. Te explico las reglas del juego: "
                    "Las ranas solo pueden saltar hacia adelante, una casilla a la vez, "
                    "o saltar sobre otra rana hacia adelante. El objetivo es intercambiar "
                    "las posiciones de ambos equipos de ranas."
                )
            elif belief_value > 0.4:
                message = (
                    "Parece que necesitas un recordatorio. Recuerda: las ranas solo pueden "
                    "moverse hacia adelante, ya sea saltando una casilla o saltando sobre otra rana."
                )
            else:
                message = (
                    "¡Bien hecho! Estás entendiendo bien las reglas del juego. "
                    "Continúa así y pronto completarás el nivel."
                )
            
            return SpeechResponse(
                message=message,
                belief_value=belief_value
            )
            
        except Exception as e:
            self.logger.error(f"Error in explain action: {e}")
            return SpeechResponse(
                message="Ocurrió un error al generar la explicación.",
                belief_value=0.0
            )
