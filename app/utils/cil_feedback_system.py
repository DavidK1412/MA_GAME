"""
Adaptive feedback system specifically designed for children with CIL.
Based on research in language development and adaptive learning.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import random
import logging
from .learning_profile import LearningProfile, LearningStyle, DifficultyLevel

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback adapted for CIL children."""
    IMMEDIATE_POSITIVE = "immediate_positive"
    GUIDED_INSTRUCTION = "guided_instruction"
    PATTERN_RECOGNITION = "pattern_recognition"
    MOTIVATIONAL = "motivational"
    CALMING = "calming"
    CELEBRATORY = "celebratory"

class CILFeedbackSystem:
    """Adaptive feedback system for children with CIL."""
    
    def __init__(self):
        self.feedback_templates = self._initialize_feedback_templates()
        self.encouragement_styles = self._initialize_encouragement_styles()
    
    def _initialize_feedback_templates(self) -> Dict[FeedbackType, List[str]]:
        """Initialize feedback templates adapted for CIL children."""
        return {
            FeedbackType.IMMEDIATE_POSITIVE: [
                "¡Muy bien! Ese fue un gran paso. 🎉",
                "¡Excelente! Estás aprendiendo muy bien. 🌟",
                "¡Perfecto! Cada movimiento te acerca más. ⭐",
                "¡Genial! Estás mejorando mucho. 🚀",
                "¡Fantástico! Ese movimiento fue muy inteligente. 🧠",
                "¡Increíble! Tu cerebro está trabajando muy bien. 💪",
                "¡Magnífico! Estás pensando como un experto. 🎯",
                "¡Sobresaliente! Tu estrategia es muy buena. 🏆"
            ],
            
            FeedbackType.GUIDED_INSTRUCTION: [
                "Recuerda: las ranas azules van hacia la derecha, las rojas hacia la izquierda. 🐸",
                "Piensa: ¿qué rana puede moverse hacia el espacio vacío? 🤔",
                "Observa: ¿hay alguna rana que pueda saltar sobre otra? 👀",
                "Mira bien: cada rana solo puede ir hacia adelante. 👁️",
                "Pregúntate: ¿cuál es el siguiente paso lógico? 💭",
                "Recuerda: no puedes saltar sobre tu propio color. ⚠️",
                "Piensa paso a paso: primero mueve una rana, luego otra. 🚶‍♂️",
                "Observa el patrón: las ranas se turnan para moverse. 🔄"
            ],
            
            FeedbackType.PATTERN_RECOGNITION: [
                "¡Muy bien! Estás viendo el patrón correcto. 👁️",
                "¡Excelente! Tu cerebro está reconociendo la secuencia. 🧠",
                "¡Perfecto! Estás entendiendo cómo funcionan las ranas. 🐸",
                "¡Genial! Estás aprendiendo la regla importante. 📚",
                "¡Fantástico! Tu mente está conectando las ideas. 🔗",
                "¡Increíble! Estás viendo la lógica del juego. 🎲",
                "¡Magnífico! Tu cerebro está creando conexiones. 🧩",
                "¡Sobresaliente! Estás desarrollando tu estrategia. 🎯"
            ],
            
            FeedbackType.MOTIVATIONAL: [
                "¡Tú puedes hacerlo! Cada intento te hace más fuerte. 💪",
                "¡No te rindas! Los grandes jugadores practican mucho. 🏃‍♂️",
                "¡Sigue intentando! Cada error es una oportunidad de aprender. 🌱",
                "¡Ánimo! Estás mejorando con cada movimiento. 📈",
                "¡Persevera! La práctica hace al maestro. 🎓",
                "¡Continúa! Tu esfuerzo se está notando. ✨",
                "¡Mantén el ritmo! Estás en el camino correcto. 🛤️",
                "¡Sigue así! Tu dedicación es admirable. 👏"
            ],
            
            FeedbackType.CALMING: [
                "Tranquilo, respira profundo. Tómate tu tiempo. 😌",
                "No te preocupes, todos aprendemos a su ritmo. 🤗",
                "Relájate, piensa con calma. Todo saldrá bien. 🧘‍♂️",
                "Respira, no hay prisa. Cada paso cuenta. 🌬️",
                "Tómate un momento, piensa despacio. ⏰",
                "No te estreses, el juego es para divertirse. 😊",
                "Relájate, tu cerebro necesita tiempo para procesar. 🧠",
                "Tranquilo, cada niño aprende diferente. 🌈"
            ],
            
            FeedbackType.CELEBRATORY: [
                "¡FELICIDADES! ¡Has completado el nivel! 🎊🎉",
                "¡INCREÍBLE! ¡Eres un campeón de las ranas! 🏆👑",
                "¡FANTÁSTICO! ¡Tu cerebro es muy inteligente! 🧠✨",
                "¡MAGNÍFICO! ¡Has demostrado ser muy hábil! 🎯🌟",
                "¡SOBRESALIENTE! ¡Eres un maestro del juego! 🎓🏅",
                "¡EXTRAORDINARIO! ¡Tu perseverancia es admirable! 💎👏",
                "¡PHENOMENAL! ¡Has superado todos los desafíos! 🚀⭐",
                "¡SENSACIONAL! ¡Eres un verdadero experto! 🎪🎭"
            ]
        }
    
    def _initialize_encouragement_styles(self) -> Dict[str, List[str]]:
        """Initialize encouragement styles for different CIL profiles."""
        return {
            "supportive": [
                "Está bien, inténtalo de nuevo. Te ayudo. 🤝",
                "No te preocupes, juntos lo lograremos. 💪",
                "Tranquilo, yo estoy aquí para ayudarte. 🤗",
                "Respira, vamos paso a paso. 🌬️",
                "No hay prisa, tómate tu tiempo. ⏰",
                "Estoy orgulloso de tu esfuerzo. 👏",
                "Cada intento cuenta, sigamos adelante. 🌱",
                "Tu valentía me impresiona. 🦁"
            ],
            
            "motivational": [
                "¡Vamos! ¡Tú puedes hacerlo! 🚀",
                "¡Sí! ¡Ese es el espíritu! ⚡",
                "¡Adelante! ¡Estás en el camino correcto! 🛤️",
                "¡Excelente actitud! ¡Sigue así! 💯",
                "¡Eso es! ¡Tu determinación es genial! 🔥",
                "¡Perfecto! ¡Tu energía es contagiosa! ⚡",
                "¡Increíble! ¡Tu entusiasmo me encanta! 🎉",
                "¡Fantástico! ¡Tu positividad es admirable! ☀️"
            ],
            
            "celebratory": [
                "¡WOW! ¡Eso fue espectacular! 🌟",
                "¡INCREÍBLE! ¡Tu talento es impresionante! 🎭",
                "¡FANTÁSTICO! ¡Eres realmente especial! ✨",
                "¡MAGNÍFICO! ¡Tu habilidad es extraordinaria! 🎪",
                "¡SOBRESALIENTE! ¡Eres un verdadero genio! 🧠",
                "¡EXTRAORDINARIO! ¡Tu creatividad es única! 🎨",
                "¡PHENOMENAL! ¡Eres absolutamente increíble! 🚀",
                "¡SENSACIONAL! ¡Tu destreza es legendaria! 👑"
            ]
        }
    
    def get_adaptive_feedback(self, game_id: str, metrics: Dict[str, Any], 
                            learning_profile: LearningProfile, 
                            last_feedback_type: Optional[FeedbackType] = None) -> Dict[str, Any]:
        """Get adaptive feedback based on CIL child's profile and current state."""
        try:
            # Determine current emotional state
            emotional_state = self._assess_emotional_state(metrics, learning_profile)
            
            # Select appropriate feedback type
            feedback_type = self._select_feedback_type(emotional_state, metrics, learning_profile, last_feedback_type)
            
            # Get feedback message
            message = self._get_feedback_message(feedback_type, learning_profile)
            
            # Add visual and verbal cues based on learning style
            visual_cues = self._get_visual_cues(learning_profile, feedback_type)
            verbal_guidance = self._get_verbal_guidance(learning_profile, feedback_type)
            
            return {
                "type": feedback_type.value,
                "message": message,
                "visual_cues": visual_cues,
                "verbal_guidance": verbal_guidance,
                "encouragement_style": learning_profile.get_encouragement_style(),
                "should_celebrate": self._should_celebrate(metrics, learning_profile),
                "next_action_hint": self._get_next_action_hint(metrics, learning_profile)
            }
            
        except Exception as e:
            logger.error(f"Error generating adaptive feedback: {e}")
            return self._get_fallback_feedback()
    
    def _assess_emotional_state(self, metrics: Dict[str, Any], profile: LearningProfile) -> str:
        """Assess the child's current emotional state."""
        success_rate = profile.success_rate
        tries_count = metrics.get('tries_count', 0)
        misses_count = metrics.get('misses_count', 0)
        buclicity = metrics.get('buclicity', 0)
        
        error_rate = misses_count / max(1, tries_count)
        
        if success_rate > 0.8 and error_rate < 0.2:
            return "confident"
        elif success_rate > 0.5 and error_rate < 0.4:
            return "engaged"
        elif success_rate > 0.3 and error_rate < 0.6:
            return "struggling"
        elif buclicity > 0.7:
            return "frustrated"
        else:
            return "confused"
    
    def _select_feedback_type(self, emotional_state: str, metrics: Dict[str, Any], 
                            profile: LearningProfile, last_feedback_type: Optional[FeedbackType]) -> FeedbackType:
        """Select the most appropriate feedback type."""
        if emotional_state == "confident":
            return FeedbackType.CELEBRATORY
        elif emotional_state == "engaged":
            return FeedbackType.IMMEDIATE_POSITIVE
        elif emotional_state == "struggling":
            return FeedbackType.GUIDED_INSTRUCTION
        elif emotional_state == "frustrated":
            return FeedbackType.CALMING
        else:  # confused
            return FeedbackType.PATTERN_RECOGNITION
    
    def _get_feedback_message(self, feedback_type: FeedbackType, profile: LearningProfile) -> str:
        """Get appropriate feedback message."""
        messages = self.feedback_templates[feedback_type]
        
        # Select message based on learning style
        if profile.learning_style == LearningStyle.VISUAL:
            # Prefer messages with visual references
            visual_messages = [msg for msg in messages if any(emoji in msg for emoji in "👀👁️🎯🔍")]
            if visual_messages:
                return random.choice(visual_messages)
        elif profile.learning_style == LearningStyle.VERBAL:
            # Prefer messages with verbal/thinking references
            verbal_messages = [msg for msg in messages if any(word in msg.lower() for word in ["piensa", "recuerda", "observa", "mira"])]
            if verbal_messages:
                return random.choice(verbal_messages)
        
        return random.choice(messages)
    
    def _get_visual_cues(self, profile: LearningProfile, feedback_type: FeedbackType) -> List[str]:
        """Get visual cues based on learning profile."""
        if not profile.should_show_visual_cues():
            return []
        
        visual_cues = []
        
        if feedback_type == FeedbackType.GUIDED_INSTRUCTION:
            visual_cues.extend([
                "🔵 Las ranas azules van hacia la derecha",
                "🔴 Las ranas rojas van hacia la izquierda",
                "⚪ El espacio vacío es donde pueden moverse",
                "🦘 Pueden saltar sobre otras ranas"
            ])
        elif feedback_type == FeedbackType.PATTERN_RECOGNITION:
            visual_cues.extend([
                "👁️ Observa el patrón de colores",
                "🔄 Mira cómo se mueven las ranas",
                "📐 Ve la secuencia lógica",
                "🧩 Conecta las piezas del rompecabezas"
            ])
        
        return visual_cues
    
    def _get_verbal_guidance(self, profile: LearningProfile, feedback_type: FeedbackType) -> List[str]:
        """Get verbal guidance based on learning profile."""
        if not profile.should_provide_verbal_guidance():
            return []
        
        guidance = []
        
        if feedback_type == FeedbackType.GUIDED_INSTRUCTION:
            guidance.extend([
                "Dime qué ves en el tablero",
                "¿Qué rana crees que puede moverse?",
                "Piensa en voz alta",
                "Explícame tu estrategia"
            ])
        elif feedback_type == FeedbackType.CALMING:
            guidance.extend([
                "Respira profundo",
                "Tómate tu tiempo",
                "No hay prisa",
                "Relájate y piensa"
            ])
        
        return guidance
    
    def _should_celebrate(self, metrics: Dict[str, Any], profile: LearningProfile) -> bool:
        """Determine if we should celebrate the child's progress."""
        success_rate = profile.success_rate
        tries_count = metrics.get('tries_count', 0)
        
        # Celebrate more frequently for CIL children
        if success_rate > 0.7:
            return True
        elif tries_count > 0 and tries_count % 3 == 0:  # Every 3 moves
            return True
        elif metrics.get('correct_moves', 0) > 0 and metrics['correct_moves'] % 2 == 0:
            return True
        
        return False
    
    def _get_next_action_hint(self, metrics: Dict[str, Any], profile: LearningProfile) -> Optional[str]:
        """Get a hint for the next action."""
        if profile.difficulty_level == DifficultyLevel.VERY_EASY:
            return "Mueve cualquier rana hacia el espacio vacío"
        elif profile.difficulty_level == DifficultyLevel.EASY:
            return "Busca una rana que pueda moverse hacia adelante"
        else:
            return None
    
    def _get_fallback_feedback(self) -> Dict[str, Any]:
        """Get fallback feedback in case of errors."""
        return {
            "type": "immediate_positive",
            "message": "¡Muy bien! Sigue intentando. 🌟",
            "visual_cues": [],
            "verbal_guidance": [],
            "encouragement_style": "supportive",
            "should_celebrate": False,
            "next_action_hint": None
        }
