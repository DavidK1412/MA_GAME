"""
Explain belief controller for providing explanations to players.
"""

from typing import Any, Dict
from controllers.base import BeliefController
from domain.models.response import SpeechResponse, Response, ResponseType
from utils.incentive_scripts import get_tries_count, get_misses_count


class ExplainController(BeliefController):
    """
    Explain belief controller that provides explanations based on player performance.
    """
    
    def __init__(self, db_client, name: str = "Explain"):
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
            # Calculate CE (Conocimiento de las reglas) based on tries and misses
            tries_count = get_tries_count(game_id, self.db_client)
            misses_count = get_misses_count(game_id, self.db_client)
            CE = (tries_count + misses_count) / 10
            
            new_values = {
                "CE": CE,
                "E": misses_count
            }
            self.values = new_values
            self.log_operation("values_updated", {"game_id": game_id, "values": new_values})
            return True
            
        except Exception as e:
            self.log_error("values_update", e, {"game_id": game_id})
            return False
    
    def action(self, game_id: str) -> Response:
        """
        Provide explanation action based on belief evaluation.
        
        Args:
            game_id: Game identifier
            
        Returns:
            SpeechResponse with explanation message
        """
        try:
            # Recalcular belief_value en memoria (sin BD)
            metrics = get_game_progress(game_id, self.db_client)
            belief_value = 0.0
            if metrics['tries_count'] > 15:
                belief_value += 0.4
            elif metrics['tries_count'] > 10:
                belief_value += 0.3
            elif metrics['tries_count'] > 5:
                belief_value += 0.2
            if metrics['misses_count'] > 5:
                belief_value += 0.3
            elif metrics['misses_count'] > 2:
                belief_value += 0.2
            if metrics['buclicity'] > 5:
                belief_value += 0.2
            skill_level = calculate_player_skill_level(game_id, self.db_client)
            if skill_level < 0.3:
                belief_value += 0.3
            elif skill_level < 0.6:
                belief_value += 0.2
            belief_value = min(1.0, belief_value)
            
            # Obtener dificultad actual sin columnas de creencias
            difficulty_id = 1
            try:
                res = self.db_client.fetch_results(
                    "SELECT difficulty_id FROM game_attempts WHERE game_id = %s AND is_active = TRUE",
                    (game_id,)
                )
                if res:
                    difficulty_id = int(res[0].get('difficulty_id', 1))
            except Exception:
                difficulty_id = 1

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
            
            # Ser más fiel: devolver explicación como SPEECH explícito
            return SpeechResponse.create_rule_reminder(message)
            
        except Exception as e:
            self.logger.error(f"Error in explain action: {e}")
            return SpeechResponse.create_rule_reminder(
                "Ocurrió un error al generar la explicación."
            )
