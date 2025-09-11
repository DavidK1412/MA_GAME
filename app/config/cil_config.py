"""
CIL-specific configuration that overrides and extends the base JSON configuration.
This ensures CIL adaptations work alongside the existing equation system.
"""

from typing import Dict, Any
import json
import os

class CILConfig:
    """Configuration manager for CIL-specific settings."""
    
    def __init__(self, base_config_path: str = "config.json"):
        self.base_config_path = base_config_path
        self.base_config = self._load_base_config()
        self.cil_overrides = self._get_cil_overrides()
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load the base configuration from JSON."""
        try:
            # Try different possible paths
            possible_paths = [
                self.base_config_path,
                f"app/{self.base_config_path}",
                f"../{self.base_config_path}",
                "config.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            
            # If no config file found, return empty dict
            print("Warning: No configuration file found, using defaults")
            return {}
        except Exception as e:
            print(f"Error loading base config: {e}")
            return {}
    
    def _get_cil_overrides(self) -> Dict[str, Any]:
        """Get CIL-specific configuration overrides."""
        return {
            "cil_adaptation": {
                "enabled": True,
                "learning_style_detection": True,
                "adaptive_equations": True,
                "dynamic_weights": True,
                "feedback_adaptation": True
            },
            "learning_profiles": {
                "update_frequency": 5,  # Update profile every 5 moves
                "attention_span_min": 2.0,  # Minimum attention span in minutes
                "attention_span_max": 10.0,  # Maximum attention span in minutes
                "frustration_threshold_min": 0.3,  # Minimum frustration threshold
                "frustration_threshold_max": 0.9,  # Maximum frustration threshold
                "success_rate_window": 10  # Window for success rate calculation
            },
            "feedback_system": {
                "immediate_feedback_threshold": 0.7,  # When to give immediate feedback
                "celebration_frequency": 0.3,  # How often to celebrate
                "calming_trigger_threshold": 0.6,  # When to use calming feedback
                "visual_cues_threshold": 0.6,  # When to show visual cues
                "verbal_guidance_threshold": 0.7  # When to provide verbal guidance
            },
            "equation_adaptations": {
                "sensitivity_adjustment_range": [0.5, 2.0],  # Range for sensitivity adjustments
                "weight_adjustment_range": [0.5, 2.0],  # Range for weight adjustments
                "learning_style_impact": 0.3,  # How much learning style affects equations
                "difficulty_impact": 0.2,  # How much difficulty affects equations
                "success_rate_impact": 0.25,  # How much success rate affects equations
                "attention_span_impact": 0.15  # How much attention span affects equations
            },
            "metrics_enhancement": {
                "buclicity_pattern_window": [2, 3],  # Window sizes for pattern analysis
                "buclicity_recency_weight": 0.7,  # Weight for recent patterns
                "buclicity_immediate_weight": 0.3,  # Weight for immediate repetition
                "branch_factor_progress_weight": 0.8,  # Weight for progress in branch factor
                "cache_ttl_adaptive": True,  # Use adaptive cache TTL
                "cache_ttl_fast": 0.5,  # TTL for frequently changing metrics
                "cache_ttl_slow": 5.0  # TTL for slowly changing metrics
            }
        }
    
    def get_adaptive_config(self, game_id: str, learning_profile: Any = None) -> Dict[str, Any]:
        """Get configuration with CIL adaptations applied."""
        config = self.base_config.copy()
        
        # Merge CIL overrides
        config.update(self.cil_overrides)
        
        # If learning profile is provided, apply dynamic adjustments
        if learning_profile:
            config = self._apply_dynamic_adjustments(config, learning_profile)
        
        return config
    
    def _apply_dynamic_adjustments(self, config: Dict[str, Any], learning_profile: Any) -> Dict[str, Any]:
        """Apply dynamic adjustments based on learning profile."""
        try:
            # Adjust feedback frequency based on learning style
            if learning_profile.learning_style.value == "kinesthetic":
                config["feedback_system"]["immediate_feedback_threshold"] *= 0.8
                config["feedback_system"]["celebration_frequency"] *= 1.2
            elif learning_profile.learning_style.value == "visual":
                config["feedback_system"]["visual_cues_threshold"] *= 0.7
            elif learning_profile.learning_style.value == "verbal":
                config["feedback_system"]["verbal_guidance_threshold"] *= 0.8
            
            # Adjust based on difficulty level
            if learning_profile.difficulty_level.value == 1:  # VERY_EASY
                config["feedback_system"]["immediate_feedback_threshold"] *= 0.6
                config["equation_adaptations"]["sensitivity_adjustment_range"] = [0.3, 1.5]
            elif learning_profile.difficulty_level.value == 4:  # CHALLENGING
                config["feedback_system"]["immediate_feedback_threshold"] *= 1.2
                config["equation_adaptations"]["sensitivity_adjustment_range"] = [0.7, 2.5]
            
            # Adjust based on success rate
            if learning_profile.success_rate < 0.3:
                config["feedback_system"]["calming_trigger_threshold"] *= 0.8
                config["equation_adaptations"]["sensitivity_adjustment_range"] = [0.3, 1.2]
            elif learning_profile.success_rate > 0.8:
                config["feedback_system"]["celebration_frequency"] *= 1.3
                config["equation_adaptations"]["sensitivity_adjustment_range"] = [0.8, 2.0]
            
            # Adjust based on attention span
            if learning_profile.attention_span < 3.0:
                config["learning_profiles"]["update_frequency"] = 3
                config["metrics_enhancement"]["cache_ttl_fast"] = 0.3
            elif learning_profile.attention_span > 8.0:
                config["learning_profiles"]["update_frequency"] = 8
                config["metrics_enhancement"]["cache_ttl_fast"] = 1.0
            
        except Exception as e:
            print(f"Error applying dynamic adjustments: {e}")
        
        return config
    
    def get_equation_override(self, belief_name: str, learning_profile: Any = None) -> str:
        """Get equation override for specific belief with CIL adaptations."""
        base_equations = {
            "Feedback": "min(1, (E*2 + B*3)/12)",
            "Advice": "min(1, (IP + R*2)/18)",
            "Explain": "min(1, (1 - CE + E*2)/6)",
            "Demonstrate": "min(1, (TPM/25 + (10-A)/12)/2)",
            "Ask": "min(1, (B*3 + TP/20)/4)"
        }
        
        if not learning_profile:
            return base_equations.get(belief_name, "min(1, 0.5)")
        
        # Apply CIL-specific modifications
        equation = base_equations.get(belief_name, "min(1, 0.5)")
        
        try:
            # Adjust based on learning style
            if learning_profile.learning_style.value == "visual" and belief_name == "Demonstrate":
                # Visual learners benefit more from demonstrations
                equation = equation.replace("/2", "/1.5")
            elif learning_profile.learning_style.value == "verbal" and belief_name == "Explain":
                # Verbal learners benefit more from explanations
                equation = equation.replace("/6", "/4")
            elif learning_profile.learning_style.value == "kinesthetic" and belief_name == "Ask":
                # Kinesthetic learners benefit from interactive questions
                equation = equation.replace("/4", "/3")
            
            # Adjust based on difficulty level
            if learning_profile.difficulty_level.value == 1:  # VERY_EASY
                # More sensitive to errors and repetition
                if belief_name == "Feedback":
                    equation = equation.replace("/12", "/8")
                elif belief_name == "Explain":
                    equation = equation.replace("/6", "/4")
            elif learning_profile.difficulty_level.value == 4:  # CHALLENGING
                # Less sensitive, focus on strategy
                if belief_name == "Advice":
                    equation = equation.replace("/18", "/15")
                elif belief_name == "Demonstrate":
                    equation = equation.replace("/2", "/2.5")
            
            # Adjust based on success rate
            if learning_profile.success_rate < 0.3:
                # More sensitive for struggling children
                equation = equation.replace("min(1,", "min(1.2,")
            elif learning_profile.success_rate > 0.8:
                # Less sensitive for successful children
                equation = equation.replace("min(1,", "min(0.8,")
                
        except Exception as e:
            print(f"Error modifying equation for {belief_name}: {e}")
        
        return equation
    
    def is_cil_enabled(self) -> bool:
        """Check if CIL adaptations are enabled."""
        return self.cil_overrides.get("cil_adaptation", {}).get("enabled", True)
    
    def get_metric_weights(self, belief_name: str, learning_profile: Any = None) -> Dict[str, float]:
        """Get adaptive metric weights for CIL children."""
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
        
        if not learning_profile:
            return base_weights
        
        # Apply CIL-specific weight adjustments
        try:
            # Adjust based on learning style
            if learning_profile.learning_style.value == "visual":
                base_weights["B"] *= 0.8  # Less emphasis on repetition
                base_weights["R"] *= 1.2  # More emphasis on branching
            elif learning_profile.learning_style.value == "verbal":
                base_weights["E"] *= 1.2  # More emphasis on errors
                base_weights["CE"] *= 1.3  # More emphasis on rule knowledge
            elif learning_profile.learning_style.value == "kinesthetic":
                base_weights["B"] *= 1.3  # More emphasis on repetition
                base_weights["TPM"] *= 0.8  # Less emphasis on time
            
            # Adjust based on difficulty level
            if learning_profile.difficulty_level.value == 1:  # VERY_EASY
                base_weights["E"] *= 1.5  # More sensitive to errors
                base_weights["B"] *= 1.3  # More sensitive to repetition
            elif learning_profile.difficulty_level.value == 4:  # CHALLENGING
                base_weights["R"] *= 1.2  # More emphasis on strategy
                base_weights["A"] *= 1.1  # More emphasis on correct moves
            
            # Adjust based on success rate
            if learning_profile.success_rate < 0.3:
                base_weights["E"] *= 1.3  # More sensitive to errors
                base_weights["B"] *= 1.2  # More sensitive to repetition
            elif learning_profile.success_rate > 0.8:
                base_weights["R"] *= 1.1  # More emphasis on strategy
                base_weights["A"] *= 1.2  # More emphasis on correct moves
                
        except Exception as e:
            print(f"Error adjusting weights: {e}")
        
        return base_weights
