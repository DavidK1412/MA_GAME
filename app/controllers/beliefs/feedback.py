"""
Feedback belief controller for providing personalized feedback to players.
"""

from typing import Any, Dict
from app.controllers.base import BeliefController
from app.domain.models.response import SpeechResponse, GameResponse
from app.utils.incentive_scripts import get_game_progress, calculate_player_skill_level


class FeedbackController(BeliefController):
    """
    Feedback belief controller that provides personalized feedback based on player performance.
    """
    
    def __init__(self, db_client, name: str = "Feedback"):
        super().__init__(db_client, name)
    
    def update_values(self, game_id: str, config: Dict[str, Any]) -> bool:
        """
        Update belief values based on comprehensive game metrics.
        
        Args:
            game_id: Game identifier
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get comprehensive game progress metrics
            metrics = get_game_progress(game_id, self.db_client)
            
            # Calculate belief value based on multiple factors
            belief_value = 0.0
            
            # Factor 1: Performance-based feedback (30% weight)
            performance_score = self._calculate_performance_score(metrics)
            belief_value += performance_score * 0.3
            
            # Factor 2: Learning progress (25% weight)
            learning_score = self._calculate_learning_score(metrics)
            belief_value += learning_score * 0.25
            
            # Factor 3: Engagement level (20% weight)
            engagement_score = self._calculate_engagement_score(metrics)
            belief_value += engagement_score * 0.2
            
            # Factor 4: Difficulty adaptation (25% weight)
            difficulty_score = self._calculate_difficulty_score(metrics)
            belief_value += difficulty_score * 0.25
            
            # Cap belief value at 1.0
            belief_value = min(1.0, max(0.0, belief_value))
            
            # Store belief value in database
            query = """
                UPDATE game_attempts 
                SET feedback_belief = %s 
                WHERE game_id = %s AND is_active = TRUE
            """
            params = (belief_value, game_id)
            
            return self.safe_execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error updating feedback belief values: {e}")
            return False
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate performance score based on game metrics."""
        score = 0.0
        
        # Tries count (lower is better)
        if metrics['tries_count'] <= 5:
            score += 1.0
        elif metrics['tries_count'] <= 10:
            score += 0.7
        elif metrics['tries_count'] <= 15:
            score += 0.4
        else:
            score += 0.1
        
        # Misses count (lower is better)
        if metrics['misses_count'] == 0:
            score += 1.0
        elif metrics['misses_count'] <= 2:
            score += 0.7
        elif metrics['misses_count'] <= 5:
            score += 0.4
        else:
            score += 0.1
        
        # Correct moves ratio
        total_moves = metrics['tries_count']
        if total_moves > 0:
            correct_ratio = metrics['correct_moves'] / total_moves
            score += correct_ratio
        
        return score / 3.0  # Normalize to 0-1
    
    def _calculate_learning_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate learning progress score."""
        score = 0.0
        
        # Buclicity (lower is better - shows learning from mistakes)
        if metrics['buclicity'] == 0:
            score += 1.0
        elif metrics['buclicity'] <= 2:
            score += 0.8
        elif metrics['buclicity'] <= 5:
            score += 0.5
        else:
            score += 0.2
        
        # Branch factor (higher shows strategic thinking)
        branch_factor = metrics['branch_factor']
        if branch_factor >= 4:
            score += 1.0
        elif branch_factor >= 2:
            score += 0.7
        elif branch_factor >= 1:
            score += 0.4
        else:
            score += 0.1
        
        # Repeated states (lower shows learning)
        if metrics['repeated_states'] == 0:
            score += 1.0
        elif metrics['repeated_states'] <= 2:
            score += 0.7
        else:
            score += 0.3
        
        return score / 3.0
    
    def _calculate_engagement_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate player engagement score."""
        score = 0.0
        
        # Time between moves (reasonable time shows engagement)
        avg_time = metrics['average_time']
        if 2 <= avg_time <= 15:  # 2-15 seconds is good engagement
            score += 1.0
        elif 1 <= avg_time <= 30:
            score += 0.7
        elif avg_time < 60:
            score += 0.4
        else:
            score += 0.1
        
        # Consistent progress (no long gaps)
        if metrics['tries_count'] > 0:
            consistency = min(1.0, 20 / metrics['tries_count'])
            score += consistency
        
        return score / 2.0
    
    def _calculate_difficulty_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate difficulty adaptation score."""
        score = 0.0
        
        # Skill level assessment
        skill_level = calculate_player_skill_level(metrics['game_id'], self.db_client)
        
        if skill_level >= 0.8:
            score += 1.0  # Ready for harder challenges
        elif skill_level >= 0.6:
            score += 0.7  # Good progress
        elif skill_level >= 0.4:
            score += 0.5  # Moderate progress
        elif skill_level >= 0.2:
            score += 0.3  # Needs help
        else:
            score += 0.1  # Struggling
        
        return score
    
    def action(self, game_id: str) -> SpeechResponse:
        """
        Provide personalized feedback action based on belief evaluation.
        
        Args:
            game_id: Game identifier
            
        Returns:
            SpeechResponse with personalized feedback
        """
        try:
            # Get current belief value and metrics
            query = """
                SELECT feedback_belief, difficulty_id 
                FROM game_attempts 
                WHERE game_id = %s AND is_active = TRUE
            """
            params = (game_id,)
            result = self.db_client.fetch_results(query, params)
            
            if not result:
                return SpeechResponse(
                    message="No se pudo obtener información del juego para generar feedback.",
                    belief_value=0.0
                )
            
            belief_value = result[0].get('feedback_belief', 0.0)
            difficulty_id = result[0].get('difficulty_id', 1)
            
            # Get current metrics for context
            metrics = get_game_progress(game_id, self.db_client)
            
            # Generate personalized feedback message
            message = self._generate_feedback_message(belief_value, metrics, difficulty_id)
            
            return SpeechResponse(
                message=message,
                belief_value=belief_value
            )
            
        except Exception as e:
            self.logger.error(f"Error in feedback action: {e}")
            return SpeechResponse(
                message="Ocurrió un error al generar el feedback personalizado.",
                belief_value=0.0
            )
    
    def _generate_feedback_message(self, belief_value: float, metrics: Dict[str, Any], difficulty_id: int) -> str:
        """Generate personalized feedback message."""
        
        if belief_value >= 0.8:
            # Excellent performance
            if difficulty_id < 3:
                return (
                    "¡Excelente trabajo! Has dominado este nivel completamente. "
                    "¿Te gustaría intentar un nivel más difícil? "
                    "Tu estrategia y precisión son impresionantes."
                )
            else:
                return (
                    "¡Increíble! Has completado el nivel más difícil. "
                    "Eres un verdadero maestro del juego de las ranas. "
                    "Tu habilidad para resolver problemas complejos es excepcional."
                )
        
        elif belief_value >= 0.6:
            # Good performance
            return (
                "¡Muy bien! Estás progresando excelentemente. "
                f"Has completado el nivel en solo {metrics['tries_count']} movimientos "
                f"con solo {metrics['misses_count']} errores. "
                "Continúa así y pronto serás un experto."
            )
        
        elif belief_value >= 0.4:
            # Moderate performance
            if metrics['misses_count'] > 3:
                return (
                    "Estás en el camino correcto, pero hay espacio para mejorar. "
                    f"Has tenido {metrics['misses_count']} errores, "
                    "lo que sugiere que podrías revisar las reglas. "
                    "¡No te rindas, cada intento te hace más fuerte!"
                )
            else:
                return (
                    "Buen progreso. Estás entendiendo las reglas del juego. "
                    f"Con {metrics['tries_count']} movimientos, "
                    "estás cerca de optimizar tu estrategia. "
                    "¡Sigue practicando!"
                )
        
        elif belief_value >= 0.2:
            # Needs improvement
            if metrics['buclicity'] > 3:
                return (
                    "Veo que te estás atascando en patrones repetitivos. "
                    "Intenta pensar en diferentes estrategias. "
                    "A veces, dar un paso atrás te ayuda a ver el camino hacia adelante. "
                    "¡Tú puedes hacerlo!"
                )
            else:
                return (
                    "Estás aprendiendo, y eso es lo importante. "
                    f"Con {metrics['tries_count']} intentos, "
                    "estás explorando diferentes soluciones. "
                    "Recuerda: las ranas solo pueden moverse hacia adelante. "
                    "¡Mantén la calma y sigue intentando!"
                )
        
        else:
            # Struggling
            return (
                "No te preocupes, todos empezamos desde algún lugar. "
                "Este juego requiere práctica y paciencia. "
                "Te sugiero revisar las reglas básicas: "
                "las ranas solo pueden saltar hacia adelante, "
                "una casilla o sobre otra rana. "
                "¡Cada intento te acerca más al éxito!"
            )
