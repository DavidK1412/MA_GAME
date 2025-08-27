"""
Ask belief controller for engaging players with interactive questions.
"""

from typing import Any, Dict, List, Optional
import random
from controllers.base import BeliefController
from domain.models.response import SpeechResponse, GameResponse, Response, ResponseType
from utils.incentive_scripts import get_game_progress, calculate_player_skill_level


class AskController(BeliefController):
    """
    Ask belief controller that engages players with interactive questions and assessments.
    """
    
    def __init__(self, db_client, name: str = "Ask"):
        super().__init__(db_client, name)
    
    def update_values(self, game_id: str, config: Dict[str, Any]) -> bool:
        """
        Update belief values based on player's need for interactive engagement.
        
        Args:
            game_id: Game identifier
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get game progress metrics
            metrics = get_game_progress(game_id, self.db_client)
            
            # Calculate belief value based on engagement needs (sin escribir en BD)
            belief_value = 0.0
            avg_time = metrics['average_time']
            if avg_time > 60:
                belief_value += 0.3
            elif avg_time > 30:
                belief_value += 0.2
            if metrics['tries_count'] > 15 and metrics['correct_moves'] < metrics['tries_count'] * 0.3:
                belief_value += 0.3
            skill_level = calculate_player_skill_level(game_id, self.db_client)
            if skill_level < 0.3:
                belief_value += 0.3
            elif skill_level < 0.5:
                belief_value += 0.2
            if metrics['buclicity'] > 5:
                belief_value += 0.2
            if self._is_player_inactive(game_id):
                belief_value += 0.2
            belief_value = min(1.0, belief_value)
            self.values = {"belief_value": belief_value, **metrics}
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating ask belief values: {e}")
            return False
    
    def _is_player_inactive(self, game_id: str) -> bool:
        """Check if the player has been inactive for a while."""
        try:
            query = """
                SELECT m.movement_time
                FROM game_attempts ga
                JOIN movements m ON ga.id = m.attempt_id
                WHERE ga.game_id = %s AND ga.is_active = TRUE
                ORDER BY m.movement_time DESC
                LIMIT 1
            """
            params = (game_id,)
            result = self.db_client.fetch_results(query, params)
            
            if not result:
                return False
            
            last_move_time = result[0]['movement_time']
            from datetime import datetime, timezone, date
            if isinstance(last_move_time, str):
                last_move_time = datetime.fromisoformat(last_move_time.replace('Z', '+00:00'))
            # Si es datetime.time, combínalo con la fecha actual
            if hasattr(last_move_time, 'hour') and not hasattr(last_move_time, 'year'):
                last_move_time = datetime.combine(date.today(), last_move_time).replace(tzinfo=timezone.utc)
            current_time = datetime.now(timezone.utc)
            time_diff = current_time - last_move_time
            
            return time_diff.total_seconds() > 300  # 5 minutes
            
        except Exception as e:
            self.logger.error(f"Error checking player inactivity: {e}")
            return False
    
    def action(self, game_id: str) -> SpeechResponse:
        """
        Provide interactive question action based on belief evaluation.
        
        Args:
            game_id: Game identifier
            
        Returns:
            SpeechResponse with interactive question
        """
        try:
            # Recalcular belief_value y contexto en memoria (sin BD)
            metrics = get_game_progress(game_id, self.db_client)
            belief_value = 0.0
            avg_time = metrics['average_time']
            if avg_time > 60:
                belief_value += 0.3
            elif avg_time > 30:
                belief_value += 0.2
            if metrics['tries_count'] > 15 and metrics['correct_moves'] < metrics['tries_count'] * 0.3:
                belief_value += 0.3
            skill_level = calculate_player_skill_level(game_id, self.db_client)
            if skill_level < 0.3:
                belief_value += 0.3
            elif skill_level < 0.5:
                belief_value += 0.2
            if metrics['buclicity'] > 5:
                belief_value += 0.2
            if self._is_player_inactive(game_id):
                belief_value += 0.2
            belief_value = min(1.0, belief_value)

            # Obtener dificultad actual sin columnas de creencias
            from typing import Optional
            difficulty_id: int = 1
            try:
                res = self.db_client.fetch_results(
                    "SELECT difficulty_id FROM game_attempts WHERE game_id = %s AND is_active = TRUE",
                    (game_id,)
                )
                if res:
                    difficulty_id = int(res[0].get('difficulty_id', 1))
            except Exception:
                difficulty_id = 1
            
            # Pregunta simple de ofrecimiento de ayuda (variaciones)
            help_prompts = [
                "¿Necesitas ayuda con el siguiente movimiento?",
                "¿Quieres que te ayude ahora?",
                "¿Te muestro una pista para el próximo paso?",
                "¿Prefieres recibir ayuda en este momento?",
                "¿Deseas asistencia para continuar?",
            ]
            message = random.choice(help_prompts)

            # Ser fiel a DecisionCenter: devolver tipo ASK con texto directo
            return Response(
                type=ResponseType.ASK,
                actions={"text": message}
            )
            
        except Exception as e:
            self.logger.error(f"Error in ask action: {e}")
            return Response(
                type=ResponseType.ASK,
                actions={"text": "Ocurrió un error al generar la pregunta interactiva."}
            )
    
    def _generate_question_message(
        self, 
        belief_value: float, 
        metrics: Dict[str, Any], 
        difficulty_id: int, 
        game_id: str
    ) -> str:
        """Generate appropriate question message based on belief value and context."""
        
        if belief_value >= 0.7:
            # High need for engagement - ask strategic questions
            return self._ask_strategic_question(metrics, difficulty_id)
        
        elif belief_value >= 0.5:
            # Moderate need - ask understanding questions
            return self._ask_understanding_question(metrics, difficulty_id)
        
        elif belief_value >= 0.3:
            # Low need - ask motivational questions
            return self._ask_motivational_question(metrics, difficulty_id)
        
        else:
            # Very low need - just check in
            return self._check_in_question(metrics, difficulty_id)
    
    def _ask_strategic_question(self, metrics: Dict[str, Any], difficulty_id: int) -> str:
        """Ask strategic questions to help player think about the game."""
        questions = [
            "¿Has notado algún patrón en los movimientos que te han funcionado mejor?",
            "¿Qué estrategia estás siguiendo para resolver este nivel?",
            "¿Has considerado que a veces mover una rana que parece no importante puede abrir nuevas posibilidades?",
            "¿Qué te parece más difícil: planificar varios pasos adelante o reaccionar a la situación actual?",
            "¿Has intentado visualizar dónde quieres que estén las ranas en 3-4 movimientos?"
        ]
        
        # Choose question based on player's current situation
        if metrics['buclicity'] > 3:
            return (
                "Veo que te estás atascando en patrones repetitivos. "
                "¿Has notado qué está causando que vuelvas a la misma posición? "
                "A veces, dar un paso atrás te ayuda a ver el camino hacia adelante."
            )
        elif metrics['misses_count'] > 5:
            return (
                "Has tenido varios movimientos incorrectos. "
                "¿Puedes recordar cuáles fueron las reglas del juego? "
                "¿Qué crees que hace que un movimiento sea válido o inválido?"
            )
        elif metrics['tries_count'] > 20:
            return (
                "Has intentado muchas veces este nivel. "
                "¿Qué crees que te está faltando para completarlo? "
                "¿Has considerado que podrías estar complicando demasiado la solución?"
            )
        else:
            import random
            return random.choice(questions)
    
    def _ask_understanding_question(self, metrics: Dict[str, Any], difficulty_id: int) -> str:
        """Ask questions to check player's understanding of the game."""
        if metrics['correct_moves'] < metrics['tries_count'] * 0.5:
            return (
                "Veo que algunos de tus movimientos no han sido correctos. "
                "¿Puedes explicarme en tus propias palabras cuáles son las reglas del juego? "
                "¿Qué crees que significa que las ranas solo pueden moverse hacia adelante?"
            )
        elif metrics['repeated_states'] > 2:
            return (
                "Has visitado algunas posiciones más de una vez. "
                "¿Por qué crees que esto está sucediendo? "
                "¿Qué podrías hacer diferente para evitar repetir estados?"
            )
        else:
            return (
                "¿Cómo te sientes con tu progreso en este nivel? "
                "¿Hay algo específico que te gustaría que te explique mejor sobre el juego?"
            )
    
    def _ask_motivational_question(self, metrics: Dict[str, Any], difficulty_id: int) -> str:
        """Ask motivational questions to keep player engaged."""
        if difficulty_id == 1:
            return (
                "¿Te está gustando el juego hasta ahora? "
                "¿Qué te parece más interesante: la lógica del puzzle o la estrategia de resolución?"
            )
        elif difficulty_id == 2:
            return (
                "¡Bien hecho llegando al nivel intermedio! "
                "¿Cómo te sientes comparado con cuando empezaste? "
                "¿Has notado que tu forma de pensar sobre el juego ha cambiado?"
            )
        else:
            return (
                "¡Estás en el nivel más difícil! "
                "¿Qué te motiva a continuar? "
                "¿Qué has aprendido de los niveles anteriores que te está ayudando ahora?"
            )
    
    def _check_in_question(self, metrics: Dict[str, Any], difficulty_id: int) -> str:
        """Simple check-in question for players doing well."""
        return (
            "¿Todo bien? Veo que estás progresando muy bien. "
            "¿Hay algo en lo que te gustaría que te ayude o prefieres continuar solo?"
        )
    
    def get_follow_up_question(self, game_id: str, player_response: str) -> str:
        """
        Generate a follow-up question based on player's response.
        
        Args:
            game_id: Game identifier
            player_response: Player's response to the previous question
            
        Returns:
            Follow-up question
        """
        try:
            # Analyze player response for keywords
            response_lower = player_response.lower()
            
            if any(word in response_lower for word in ['reglas', 'regla', 'normas']):
                return (
                    "Perfecto, entiendes las reglas. "
                    "¿Puedes darme un ejemplo de un movimiento que sería válido "
                    "y otro que sería inválido desde tu posición actual?"
                )
            
            elif any(word in response_lower for word in ['estratégia', 'estrategia', 'plan']):
                return (
                    "¡Excelente que estés pensando estratégicamente! "
                    "¿Cuántos pasos adelante sueles planificar cuando juegas?"
                )
            
            elif any(word in response_lower for word in ['dificil', 'difícil', 'complicado']):
                return (
                    "Entiendo que te parece difícil. "
                    "¿Qué parte específica te resulta más complicada? "
                    "¿Es la planificación, recordar las reglas, o algo más?"
                )
            
            elif any(word in response_lower for word in ['ayuda', 'ayudar', 'ayudame']):
                return (
                    "¡Por supuesto! Estoy aquí para ayudarte. "
                    "¿Te gustaría que te explique algo específico o prefieres que te dé una pista?"
                )
            
            else:
                return (
                    "Gracias por tu respuesta. "
                    "¿Hay algo más en lo que pueda ayudarte con el juego?"
                )
                
        except Exception as e:
            self.logger.error(f"Error generating follow-up question: {e}")
            return "Gracias por tu respuesta. ¿Hay algo más en lo que pueda ayudarte?"
    
    def assess_player_understanding(self, game_id: str, player_response: str) -> Dict[str, Any]:
        """
        Assess player's understanding based on their response.
        
        Args:
            game_id: Game identifier
            player_response: Player's response to questions
            
        Returns:
            Dictionary with understanding assessment
        """
        try:
            assessment = {
                'understanding_level': 0.0,
                'confidence_level': 0.0,
                'engagement_level': 0.0,
                'suggested_help': []
            }
            
            response_lower = player_response.lower()
            
            # Assess understanding level
            if any(word in response_lower for word in ['reglas', 'adelante', 'saltar', 'rana']):
                assessment['understanding_level'] += 0.3
            
            if any(word in response_lower for word in ['estrategia', 'plan', 'pasos', 'objetivo']):
                assessment['understanding_level'] += 0.3
            
            if any(word in response_lower for word in ['dificil', 'complicado', 'confuso']):
                assessment['understanding_level'] += 0.2
            
            if any(word in response_lower for word in ['ayuda', 'ayudar', 'explicar']):
                assessment['understanding_level'] += 0.2
            
            # Assess confidence level
            if any(word in response_lower for word in ['puedo', 'sé', 'entiendo', 'claro']):
                assessment['confidence_level'] += 0.4
            
            if any(word in response_lower for word in ['creo', 'pienso', 'supongo']):
                assessment['confidence_level'] += 0.2
            
            if any(word in response_lower for word in ['no sé', 'confuso', 'duda']):
                assessment['confidence_level'] -= 0.3
            
            # Assess engagement level
            if len(player_response) > 20:
                assessment['engagement_level'] += 0.3
            
            if any(word in response_lower for word in ['gracias', 'ayuda', 'interesante']):
                assessment['engagement_level'] += 0.2
            
            # Generate suggested help
            if assessment['understanding_level'] < 0.5:
                assessment['suggested_help'].append('explicar_reglas')
            
            if assessment['confidence_level'] < 0.3:
                assessment['suggested_help'].append('dar_apoyo')
            
            if assessment['engagement_level'] < 0.4:
                assessment['suggested_help'].append('aumentar_engagement')
            
            # Cap values at 1.0
            assessment['understanding_level'] = min(1.0, max(0.0, assessment['understanding_level']))
            assessment['confidence_level'] = min(1.0, max(0.0, assessment['confidence_level']))
            assessment['engagement_level'] = min(1.0, max(0.0, assessment['engagement_level']))
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing player understanding: {e}")
            return {
                'understanding_level': 0.0,
                'confidence_level': 0.0,
                'engagement_level': 0.0,
                'suggested_help': []
            }
