"""
Dynamic equation system for CIL children.
Adapts belief equations based on individual learning profiles and progress.
"""

from typing import Dict, Any, Optional
import logging
from .learning_profile import LearningProfile, LearningStyle, DifficultyLevel
from config.cil_config import CILConfig

logger = logging.getLogger(__name__)

class CILEquationSystem:
    """Dynamic equation system for children with CIL."""
    
    def __init__(self):
        self.cil_config = CILConfig()
        self.base_equations = self._initialize_base_equations()
        self.adaptation_factors = self._initialize_adaptation_factors()
    
    def _initialize_base_equations(self) -> Dict[str, str]:
        """Initialize base equations for each belief controller."""
        return {
            "Feedback": "min(1, (E*2 + B*3)/12)",
            "Advice": "min(1, (IP + R*2)/18)",
            "Explain": "min(1, (1 - CE + E*2)/6)",
            "Demonstrate": "min(1, (TPM/25 + (10-A)/12)/2)",
            "Ask": "min(1, (B*3 + TP/20)/4)"
        }
    
    def _initialize_adaptation_factors(self) -> Dict[str, Dict[str, float]]:
        """Initialize adaptation factors for different CIL profiles."""
        return {
            "visual_learner": {
                "Demonstrate": 1.3,  # Visual learners benefit more from demonstrations
                "Explain": 1.1,      # Slight increase in explanations
                "Feedback": 0.9,     # Less verbal feedback
                "Advice": 0.8,       # Less abstract advice
                "Ask": 1.0           # Neutral
            },
            "verbal_learner": {
                "Explain": 1.4,      # Verbal learners benefit from explanations
                "Ask": 1.2,          # Questions help verbal processing
                "Feedback": 1.1,     # Verbal feedback is helpful
                "Advice": 1.0,       # Neutral
                "Demonstrate": 0.8   # Less visual demonstrations
            },
            "kinesthetic_learner": {
                "Demonstrate": 1.5,  # Hands-on demonstrations are crucial
                "Ask": 1.3,          # Interactive questions
                "Feedback": 1.2,     # Immediate feedback
                "Advice": 0.7,       # Less abstract advice
                "Explain": 0.9       # Less verbal explanations
            },
            "mixed_learner": {
                "Feedback": 1.1,     # Slight increase in all
                "Advice": 1.1,
                "Explain": 1.1,
                "Demonstrate": 1.1,
                "Ask": 1.1
            }
        }
    
    def get_adaptive_equation(self, belief_name: str, metrics: Dict[str, Any], 
                            learning_profile: LearningProfile) -> str:
        """Get adaptive equation based on CIL child's profile."""
        try:
            # Check if CIL is enabled
            if not self.cil_config.is_cil_enabled():
                return self.base_equations.get(belief_name, "min(1, 0.5)")
            
            # Get equation override from CIL config
            equation_override = self.cil_config.get_equation_override(belief_name, learning_profile)
            
            # If override is different from base, use it
            base_equation = self.base_equations.get(belief_name, "min(1, 0.5)")
            if equation_override != base_equation:
                logger.debug(f"Using CIL equation override for {belief_name}: {equation_override}")
                return equation_override
            
            # Otherwise, use the original adaptive logic
            # Determine learning style category
            style_category = self._get_style_category(learning_profile.learning_style)
            
            # Get adaptation factors
            factors = self.adaptation_factors.get(style_category, {})
            adaptation_factor = factors.get(belief_name, 1.0)
            
            # Apply difficulty-based adjustments
            difficulty_factor = self._get_difficulty_factor(learning_profile.difficulty_level)
            
            # Apply success rate adjustments
            success_factor = self._get_success_factor(learning_profile.success_rate)
            
            # Apply attention span adjustments
            attention_factor = self._get_attention_factor(learning_profile.attention_span)
            
            # Calculate final adaptation
            total_adaptation = adaptation_factor * difficulty_factor * success_factor * attention_factor
            
            # Modify equation based on adaptation
            if total_adaptation > 1.2:
                # Increase sensitivity (lower threshold)
                modified_equation = self._increase_sensitivity(base_equation, total_adaptation)
            elif total_adaptation < 0.8:
                # Decrease sensitivity (higher threshold)
                modified_equation = self._decrease_sensitivity(base_equation, total_adaptation)
            else:
                modified_equation = base_equation
            
            logger.debug(f"Adaptive equation for {belief_name}: {modified_equation} (factor: {total_adaptation:.2f})")
            return modified_equation
            
        except Exception as e:
            logger.error(f"Error generating adaptive equation: {e}")
            return self.base_equations.get(belief_name, "min(1, 0.5)")
    
    def _get_style_category(self, learning_style: LearningStyle) -> str:
        """Get style category for adaptation factors."""
        if learning_style == LearningStyle.VISUAL:
            return "visual_learner"
        elif learning_style == LearningStyle.VERBAL:
            return "verbal_learner"
        elif learning_style == LearningStyle.KINESTHETIC:
            return "kinesthetic_learner"
        else:
            return "mixed_learner"
    
    def _get_difficulty_factor(self, difficulty_level: DifficultyLevel) -> float:
        """Get difficulty-based adaptation factor."""
        factors = {
            DifficultyLevel.VERY_EASY: 1.3,    # More sensitive for easier levels
            DifficultyLevel.EASY: 1.1,
            DifficultyLevel.MODERATE: 1.0,
            DifficultyLevel.CHALLENGING: 0.8   # Less sensitive for challenging levels
        }
        return factors.get(difficulty_level, 1.0)
    
    def _get_success_factor(self, success_rate: float) -> float:
        """Get success rate-based adaptation factor."""
        if success_rate < 0.3:
            return 1.3  # More sensitive for struggling children
        elif success_rate < 0.6:
            return 1.1  # Slightly more sensitive
        elif success_rate > 0.8:
            return 0.9  # Less sensitive for successful children
        else:
            return 1.0  # Neutral
    
    def _get_attention_factor(self, attention_span: float) -> float:
        """Get attention span-based adaptation factor."""
        if attention_span < 3.0:
            return 1.2  # More frequent interventions for short attention
        elif attention_span > 8.0:
            return 0.8  # Less frequent interventions for long attention
        else:
            return 1.0  # Neutral
    
    def _increase_sensitivity(self, equation: str, factor: float) -> str:
        """Increase equation sensitivity by lowering thresholds."""
        # This is a simplified approach - in practice, you'd parse and modify the equation
        if "min(1," in equation:
            # Extract the divisor and reduce it
            parts = equation.split("/")
            if len(parts) > 1:
                divisor = float(parts[1].replace(")", ""))
                new_divisor = divisor / factor
                return equation.replace(str(divisor), str(new_divisor))
        return equation
    
    def _decrease_sensitivity(self, equation: str, factor: float) -> str:
        """Decrease equation sensitivity by raising thresholds."""
        # This is a simplified approach - in practice, you'd parse and modify the equation
        if "min(1," in equation:
            # Extract the divisor and increase it
            parts = equation.split("/")
            if len(parts) > 1:
                divisor = float(parts[1].replace(")", ""))
                new_divisor = divisor * factor
                return equation.replace(str(divisor), str(new_divisor))
        return equation
    
    def get_adaptive_weights(self, belief_name: str, learning_profile: LearningProfile) -> Dict[str, float]:
        """Get adaptive weights for equation variables."""
        # Use CIL config for weights if available
        if self.cil_config.is_cil_enabled():
            return self.cil_config.get_metric_weights(belief_name, learning_profile)
        
        # Fallback to original logic
        base_weights = {
            "E": 1.0,   # Errors
            "B": 1.0,   # Buclicity
            "IP": 1.0,  # Intentos por partida
            "R": 1.0,   # Ramificación
            "CE": 1.0,  # Conocimiento de reglas
            "TPM": 1.0, # Tiempo por movimiento
            "A": 1.0,   # Aserciones
            "TP": 1.0   # Tiempo promedio
        }
        
        # Adjust weights based on learning style
        if learning_profile.learning_style == LearningStyle.VISUAL:
            base_weights["B"] *= 0.8  # Less emphasis on repetition for visual learners
            base_weights["R"] *= 1.2  # More emphasis on branching for visual learners
        elif learning_profile.learning_style == LearningStyle.VERBAL:
            base_weights["E"] *= 1.2  # More emphasis on errors for verbal learners
            base_weights["CE"] *= 1.3  # More emphasis on rule knowledge
        elif learning_profile.learning_style == LearningStyle.KINESTHETIC:
            base_weights["B"] *= 1.3  # More emphasis on repetition for kinesthetic learners
            base_weights["TPM"] *= 0.8  # Less emphasis on time for kinesthetic learners
        
        # Adjust weights based on difficulty level
        if learning_profile.difficulty_level == DifficultyLevel.VERY_EASY:
            base_weights["E"] *= 1.5  # More sensitive to errors
            base_weights["B"] *= 1.3  # More sensitive to repetition
        elif learning_profile.difficulty_level == DifficultyLevel.CHALLENGING:
            base_weights["R"] *= 1.2  # More emphasis on strategy
            base_weights["A"] *= 1.1  # More emphasis on correct moves
        
        return base_weights
