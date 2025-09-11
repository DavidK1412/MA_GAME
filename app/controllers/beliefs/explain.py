"""
Explain belief controller for providing explanations to players.
"""

from typing import Any, Dict
from controllers.base import BeliefController
from domain.models.response import SpeechResponse, Response, ResponseType
from utils.incentive_scripts import get_tries_count, get_misses_count, get_game_progress, calculate_player_skill_level


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
            
            # En los primeros 2 movimientos, dar prioridad alta a Explain
            if tries_count <= 2:
                # Valores que resulten en una puntuación alta para Explain
                CE = 0.1  # Conocimiento bajo = más explicaciones necesarias
                E = 0     # Pocos errores al inicio
                new_values = {
                    "CE": CE,
                    "E": E
                }
                self.values = new_values
                self.log_operation("values_updated_early_moves", {
                    "game_id": game_id, 
                    "values": new_values,
                    "tries_count": tries_count,
                    "reason": "Primeros 2 movimientos - Explain priorizado"
                })
                return True
            
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
            # Obtener el número de intentos actuales
            tries_count = get_tries_count(game_id, self.db_client)
            
            # En los primeros 2 movimientos, dar explicaciones básicas de las reglas
            if tries_count <= 2:
                import random
                
                # Mensajes específicos para los primeros movimientos
                early_messages = [
                    "¡Bienvenido al juego de las ranas! 🐸 Las ranas azules van hacia la derecha y las rojas hacia la izquierda.",
                    "Recuerda: las ranas solo pueden moverse hacia adelante, una casilla o saltando sobre otra rana.",
                    "¡Perfecto! El objetivo es intercambiar las posiciones de ambos equipos de ranas.",
                    "Las ranas no pueden retroceder, solo avanzar hacia su destino final.",
                    "¡Excelente! Usa el espacio vacío para ayudar a las ranas a moverse.",
                    "Recuerda: puedes saltar sobre una rana del otro equipo, pero no sobre las tuyas.",
                    "¡Muy bien! Cada movimiento debe acercar a las ranas a sus posiciones finales.",
                    "Las ranas trabajan en equipo: cada una debe llegar al lado opuesto del tablero."
                ]
                
                message = random.choice(early_messages)
                return SpeechResponse.create_rule_reminder(message)
            
            # Para movimientos posteriores, usar la lógica original
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
