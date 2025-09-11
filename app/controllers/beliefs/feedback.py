"""
Feedback belief controller for providing personalized feedback to players.
"""

from typing import Any, Dict
from controllers.base import BeliefController
from domain.models.response import SpeechResponse, GameResponse
from utils.incentive_scripts import get_misses_count, get_buclicity, get_game_progress, calculate_player_skill_level
from utils.learning_profile import LearningProfile
from utils.cil_feedback_system import CILFeedbackSystem


class FeedbackController(BeliefController):
    """
    Feedback belief controller that provides personalized feedback based on player performance.
    """
    
    def __init__(self, db_client, name: str = "Feedback"):
        super().__init__(db_client, name)
        self.cil_feedback_system = CILFeedbackSystem()
    
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
                "E": get_misses_count(game_id, self.db_client),
                "B": get_buclicity(game_id, self.db_client)
            }
            self.values = new_values
            self.log_operation("values_updated", {"game_id": game_id, "values": new_values})
            return True
            
        except Exception as e:
            self.log_error("values_update", e, {"game_id": game_id})
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
        
        # Skill level assessment (usar game_id externo si está disponible en metrics)
        game_id_val = metrics.get('game_id') if isinstance(metrics, dict) else None
        try:
            skill_level = calculate_player_skill_level(game_id_val, self.db_client) if game_id_val else 0.5
        except Exception:
            skill_level = 0.5
        
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
        Provide personalized feedback action based on belief evaluation for CIL children.
        
        Args:
            game_id: Game identifier
            
        Returns:
            SpeechResponse with personalized feedback
        """
        try:
            # Get comprehensive metrics
            metrics = get_game_progress(game_id, self.db_client)
            
            # Create or update learning profile
            learning_profile = LearningProfile(game_id)
            learning_profile.update_from_metrics(metrics)
            
            # Get adaptive feedback using CIL system
            feedback_data = self.cil_feedback_system.get_adaptive_feedback(
                game_id, metrics, learning_profile
            )
            
            # Create enhanced response with visual and verbal cues
            message = feedback_data["message"]
            
            # Add visual cues if appropriate
            if feedback_data.get("visual_cues"):
                visual_cues_text = " ".join(feedback_data["visual_cues"])
                message += f" {visual_cues_text}"
            
            # Add verbal guidance if appropriate
            if feedback_data.get("verbal_guidance"):
                verbal_guidance_text = " ".join(feedback_data["verbal_guidance"])
                message += f" {verbal_guidance_text}"
            
            # Add next action hint if available
            if feedback_data.get("next_action_hint"):
                message += f" 💡 {feedback_data['next_action_hint']}"
            
            return SpeechResponse.create_encouragement(message)
            
        except Exception as e:
            self.logger.error(f"Error in CIL feedback action: {e}")
            return SpeechResponse.create_encouragement(
                "¡Muy bien! Sigue intentando. 🌟"
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
                    "Estás cerca de optimizar tu estrategia. "
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
                    "Estás explorando diferentes soluciones. "
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
