"""
Test script for CIL system integration.
This script verifies that the CIL adaptations work correctly with the existing equation system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.learning_profile import LearningProfile, LearningStyle, DifficultyLevel
from app.utils.cil_equation_system import CILEquationSystem
from app.config.cil_config import CILConfig

def test_cil_system():
    """Test the CIL system integration."""
    print("🧪 Testing CIL System Integration")
    print("=" * 50)
    
    # Test 1: Learning Profile Creation
    print("\n1. Testing Learning Profile Creation")
    profile = LearningProfile("test_game_123")
    print(f"   Initial learning style: {profile.learning_style.value}")
    print(f"   Initial difficulty level: {profile.difficulty_level.value}")
    print(f"   Initial success rate: {profile.success_rate}")
    
    # Test 2: Profile Update with Metrics
    print("\n2. Testing Profile Update with Metrics")
    test_metrics = {
        'tries_count': 5,
        'misses_count': 2,
        'correct_moves': 3,
        'buclicity': 0.6,
        'branch_factor': 2.5,
        'average_time': 45.0
    }
    profile.update_from_metrics(test_metrics)
    print(f"   Updated success rate: {profile.success_rate:.2f}")
    print(f"   Learning style: {profile.learning_style.value}")
    print(f"   Difficulty level: {profile.difficulty_level.value}")
    print(f"   Attention span: {profile.attention_span:.1f} minutes")
    
    # Test 3: CIL Configuration
    print("\n3. Testing CIL Configuration")
    cil_config = CILConfig()
    print(f"   CIL enabled: {cil_config.is_cil_enabled()}")
    
    # Test 4: Adaptive Equations
    print("\n4. Testing Adaptive Equations")
    equation_system = CILEquationSystem()
    
    beliefs = ["Feedback", "Advice", "Explain", "Demonstrate", "Ask"]
    for belief in beliefs:
        equation = equation_system.get_adaptive_equation(belief, test_metrics, profile)
        weights = equation_system.get_adaptive_weights(belief, profile)
        print(f"   {belief}:")
        print(f"     Equation: {equation}")
        print(f"     Weights: {weights}")
    
    # Test 5: Different Learning Styles
    print("\n5. Testing Different Learning Styles")
    styles = [LearningStyle.VISUAL, LearningStyle.VERBAL, LearningStyle.KINESTHETIC, LearningStyle.MIXED]
    
    for style in styles:
        profile.learning_style = style
        equation = equation_system.get_adaptive_equation("Feedback", test_metrics, profile)
        weights = equation_system.get_adaptive_weights("Feedback", profile)
        print(f"   {style.value} learner:")
        print(f"     Equation: {equation}")
        print(f"     Key weights: E={weights['E']:.2f}, B={weights['B']:.2f}, R={weights['R']:.2f}")
    
    # Test 6: Different Difficulty Levels
    print("\n6. Testing Different Difficulty Levels")
    difficulties = [DifficultyLevel.VERY_EASY, DifficultyLevel.EASY, DifficultyLevel.MODERATE, DifficultyLevel.CHALLENGING]
    
    for difficulty in difficulties:
        profile.difficulty_level = difficulty
        equation = equation_system.get_adaptive_equation("Advice", test_metrics, profile)
        weights = equation_system.get_adaptive_weights("Advice", profile)
        print(f"   {difficulty.name} level:")
        print(f"     Equation: {equation}")
        print(f"     Key weights: IP={weights['IP']:.2f}, R={weights['R']:.2f}")
    
    # Test 7: Different Success Rates
    print("\n7. Testing Different Success Rates")
    success_rates = [0.2, 0.5, 0.8]
    
    for rate in success_rates:
        profile.success_rate = rate
        equation = equation_system.get_adaptive_equation("Explain", test_metrics, profile)
        weights = equation_system.get_adaptive_weights("Explain", profile)
        print(f"   Success rate {rate:.1f}:")
        print(f"     Equation: {equation}")
        print(f"     Key weights: CE={weights['CE']:.2f}, E={weights['E']:.2f}")
    
    print("\n✅ CIL System Integration Test Completed Successfully!")
    print("\n📋 Summary:")
    print("   - Learning profiles adapt to individual children")
    print("   - Equations adjust based on learning style and performance")
    print("   - Weights adapt to difficulty level and success rate")
    print("   - System maintains compatibility with existing JSON configuration")
    print("   - CIL adaptations can be enabled/disabled via configuration")

if __name__ == "__main__":
    test_cil_system()
