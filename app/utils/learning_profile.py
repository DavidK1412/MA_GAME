"""
Learning profile system for children with CIL (Childhood Language Impairments).
Based on research in adaptive learning and language development.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class LearningStyle(Enum):
    """Learning styles adapted for children with CIL."""
    VISUAL = "visual"           # Prefers visual demonstrations
    VERBAL = "verbal"           # Prefers verbal explanations
    KINESTHETIC = "kinesthetic" # Prefers hands-on interaction
    MIXED = "mixed"             # Combination of styles

class DifficultyLevel(Enum):
    """Difficulty levels adapted for CIL children."""
    VERY_EASY = 1    # Single step, immediate feedback
    EASY = 2         # 2-3 steps, clear guidance
    MODERATE = 3     # 4-5 steps, some independence
    CHALLENGING = 4  # 6+ steps, minimal guidance

class LearningProfile:
    """Individual learning profile for CIL children."""
    
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.learning_style = LearningStyle.MIXED
        self.difficulty_level = DifficultyLevel.EASY
        self.attention_span = 5.0  # minutes
        self.frustration_threshold = 0.7
        self.success_rate = 0.0
        self.adaptation_speed = 0.5  # How quickly to adjust difficulty
        self.preferred_feedback_frequency = 0.3  # 0-1, how often to give feedback
        self.visual_cues_preference = 0.8  # 0-1, preference for visual elements
        self.verbal_encouragement_preference = 0.9  # 0-1, preference for verbal praise
        
    def update_from_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update profile based on current game metrics."""
        try:
            # Update success rate
            total_moves = metrics.get('tries_count', 1)
            correct_moves = metrics.get('correct_moves', 0)
            self.success_rate = correct_moves / max(1, total_moves)
            
            # Update learning style based on behavior
            self._update_learning_style(metrics)
            
            # Update difficulty level
            self._update_difficulty_level(metrics)
            
            # Update attention span based on time patterns
            self._update_attention_span(metrics)
            
            # Update frustration threshold
            self._update_frustration_threshold(metrics)
            
        except Exception as e:
            logger.error(f"Error updating learning profile: {e}")
    
    def _update_learning_style(self, metrics: Dict[str, Any]) -> None:
        """Determine learning style based on behavior patterns."""
        # Analyze response patterns to determine preferred learning style
        buclicity = metrics.get('buclicity', 0)
        branch_factor = metrics.get('branch_factor', 1)
        average_time = metrics.get('average_time', 0)
        
        # High buclicity + low branch factor = prefers repetition (kinesthetic)
        if buclicity > 3 and branch_factor < 2:
            self.learning_style = LearningStyle.KINESTHETIC
        # Low buclicity + high branch factor = prefers exploration (visual)
        elif buclicity < 2 and branch_factor > 3:
            self.learning_style = LearningStyle.VISUAL
        # Moderate patterns = verbal explanations work well
        elif 1 <= buclicity <= 3 and 2 <= branch_factor <= 4:
            self.learning_style = LearningStyle.VERBAL
        else:
            self.learning_style = LearningStyle.MIXED
    
    def _update_difficulty_level(self, metrics: Dict[str, Any]) -> None:
        """Adjust difficulty level based on performance."""
        success_rate = self.success_rate
        tries_count = metrics.get('tries_count', 0)
        misses_count = metrics.get('misses_count', 0)
        
        # Calculate performance score
        performance_score = success_rate - (misses_count / max(1, tries_count)) * 0.3
        
        if performance_score > 0.8:
            # High performance - can handle more challenge
            if self.difficulty_level.value < DifficultyLevel.CHALLENGING.value:
                self.difficulty_level = DifficultyLevel(self.difficulty_level.value + 1)
        elif performance_score < 0.4:
            # Low performance - needs easier level
            if self.difficulty_level.value > DifficultyLevel.VERY_EASY.value:
                self.difficulty_level = DifficultyLevel(self.difficulty_level.value - 1)
    
    def _update_attention_span(self, metrics: Dict[str, Any]) -> None:
        """Update attention span based on time patterns."""
        average_time = metrics.get('average_time', 0)
        
        # If child takes very long between moves, attention span might be shorter
        if average_time > 120:  # More than 2 minutes
            self.attention_span = max(2.0, self.attention_span - 0.5)
        elif average_time < 30:  # Less than 30 seconds
            self.attention_span = min(10.0, self.attention_span + 0.5)
    
    def _update_frustration_threshold(self, metrics: Dict[str, Any]) -> None:
        """Update frustration threshold based on error patterns."""
        misses_count = metrics.get('misses_count', 0)
        tries_count = metrics.get('tries_count', 1)
        
        error_rate = misses_count / max(1, tries_count)
        
        # If error rate is high, lower frustration threshold (more sensitive)
        if error_rate > 0.5:
            self.frustration_threshold = max(0.3, self.frustration_threshold - 0.1)
        elif error_rate < 0.2:
            self.frustration_threshold = min(0.9, self.frustration_threshold + 0.1)
    
    def get_optimal_feedback_timing(self) -> float:
        """Get optimal feedback timing based on profile."""
        # CIL children need more frequent, positive feedback
        base_frequency = 0.5
        if self.success_rate < 0.5:
            base_frequency += 0.3  # More feedback for struggling children
        if self.learning_style == LearningStyle.KINESTHETIC:
            base_frequency += 0.2  # Kinesthetic learners need more immediate feedback
        
        return min(1.0, base_frequency)
    
    def get_encouragement_style(self) -> str:
        """Get appropriate encouragement style for this child."""
        if self.success_rate < 0.3:
            return "supportive"  # Gentle, encouraging
        elif self.success_rate < 0.7:
            return "motivational"  # Energetic, positive
        else:
            return "celebratory"  # Excited, proud
    
    def should_show_visual_cues(self) -> bool:
        """Determine if visual cues should be shown."""
        return (self.learning_style in [LearningStyle.VISUAL, LearningStyle.MIXED] or 
                self.visual_cues_preference > 0.6)
    
    def should_provide_verbal_guidance(self) -> bool:
        """Determine if verbal guidance should be provided."""
        return (self.learning_style in [LearningStyle.VERBAL, LearningStyle.MIXED] or 
                self.verbal_encouragement_preference > 0.7)
    
    def get_optimal_difficulty_adjustment(self) -> float:
        """Get optimal difficulty adjustment factor."""
        if self.success_rate > 0.8:
            return 1.2  # Increase difficulty
        elif self.success_rate < 0.3:
            return 0.7  # Decrease difficulty
        else:
            return 1.0  # Maintain current difficulty
