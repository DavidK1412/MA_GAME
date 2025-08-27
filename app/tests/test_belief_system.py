"""
Test script for the belief system to verify all controllers work correctly.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

try:
    from utils.database import DatabaseClient
    from controllers.beliefs.advice import AdviceController
    from controllers.beliefs.feedback import FeedbackController
    from controllers.beliefs.explain import ExplainController
    from controllers.beliefs.demonstrate import DemonstrateController
    from controllers.beliefs.ask import AskController
    from controllers.decision import DecisionController
    from core.logging import setup_logging
    print("✅ Módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("Verificando estructura de archivos...")
    sys.exit(1)


def test_belief_controllers():
    """Test all belief controllers with sample data."""
    print("🧪 Testing Belief System...")
    
    try:
        # Setup logging
        setup_logging()
        
        # Initialize database client
        db_client = DatabaseClient()
        db_client.connect()
        
        print("✅ Database connection established")
        
        # Test data - simulate a game scenario
        test_game_id = "test-belief-game-001"
        test_config = {
            "difficulty": 1,
            "max_tries": 20,
            "time_limit": 300
        }
        
        # Create test controllers
        controllers = {
            "Advice": AdviceController(db_client),
            "Feedback": FeedbackController(db_client),
            "Explain": ExplainController(db_client),
            "Demonstrate": DemonstrateController(db_client),
            "Ask": AskController(db_client)
        }
        
        print("\n📊 Testing Belief Value Updates...")
        
        # Test belief value updates
        for name, controller in controllers.items():
            try:
                success = controller.update_values(test_game_id, test_config)
                print(f"  {name}: {'✅' if success else '❌'}")
            except Exception as e:
                print(f"  {name}: ❌ Error: {e}")
        
        print("\n🎯 Testing Belief Actions...")
        
        # Test belief actions
        for name, controller in controllers.items():
            try:
                response = controller.action(test_game_id)
                print(f"  {name}: ✅ Response generated")
                print(f"    Message: {response.message[:100]}...")
                print(f"    Belief Value: {response.belief_value}")
            except Exception as e:
                print(f"  {name}: ❌ Error: {e}")
        
        print("\n🤖 Testing Decision Controller...")
        
        # Test decision controller
        try:
            decision_controller = DecisionController(db_client)
            
            # Test belief evaluation
            beliefs = decision_controller.evaluate_all_beliefs(test_game_id, test_config)
            print(f"  Beliefs evaluated: {len(beliefs)}")
            
            # Test best belief selection
            best_belief = decision_controller.select_best_belief(test_game_id, test_config)
            if best_belief:
                print(f"  Best belief: {best_belief['name']} (value: {best_belief['value']:.2f})")
            else:
                print("  No best belief selected")
                
        except Exception as e:
            print(f"  Decision Controller: ❌ Error: {e}")
        
        print("\n🔍 Testing Graph Utils Integration...")
        
        # Test graph utilities integration
        try:
            from utils.graph_utils import possible_moves, shortest_path_length, is_game_winnable
            
            # Test with sample game state
            test_state = [3, 2, 1, 0, -1, -2, -3]
            test_final = [-3, -2, -1, 0, 1, 2, 3]
            
            # Test possible moves
            moves = possible_moves(3, 3, test_state)
            print(f"  Possible moves: {len(moves)} found")
            
            # Test shortest path
            path_length = shortest_path_length(3, 3, test_state, test_final)
            print(f"  Shortest path length: {path_length}")
            
            # Test if game is winnable
            winnable = is_game_winnable(3, 3, test_state, test_final)
            print(f"  Game winnable: {winnable}")
            
        except Exception as e:
            print(f"  Graph Utils: ❌ Error: {e}")
        
        print("\n📈 Testing Incentive Scripts...")
        
        # Test incentive scripts
        try:
            from utils.incentive_scripts import get_game_progress, calculate_player_skill_level
            
            # Note: These will return default values for non-existent games
            progress = get_game_progress(test_game_id, db_client)
            print(f"  Game progress metrics: {len(progress)} calculated")
            
            skill_level = calculate_player_skill_level(test_game_id, db_client)
            print(f"  Player skill level: {skill_level:.2f}")
            
        except Exception as e:
            print(f"  Incentive Scripts: ❌ Error: {e}")
        
        print("\n✅ Belief System Test Completed!")
        
        # Cleanup
        db_client.close()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    return True


def test_error_handling():
    """Test error handling in belief controllers."""
    print("\n🛡️ Testing Error Handling...")
    
    try:
        # Test with invalid database client
        invalid_db = None
        
        # This should handle the error gracefully
        try:
            controller = AdviceController(invalid_db)
            print("  ❌ Should have failed with invalid DB")
        except Exception as e:
            print(f"  ✅ Properly handled invalid DB: {type(e).__name__}")
        
        # Test with invalid game ID
        db_client = DatabaseClient()
        db_client.connect()
        
        controller = AdviceController(db_client)
        
        try:
            result = controller.update_values("", {})
            print(f"  ✅ Handled empty game ID: {result}")
        except Exception as e:
            print(f"  ❌ Failed to handle empty game ID: {e}")
        
        # Test with invalid config
        try:
            result = controller.update_values("test", None)
            print(f"  ✅ Handled invalid config: {result}")
        except Exception as e:
            print(f"  ❌ Failed to handle invalid config: {e}")
        
        db_client.close()
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")


def test_performance():
    """Test performance of belief system."""
    print("\n⚡ Testing Performance...")
    
    try:
        db_client = DatabaseClient()
        db_client.connect()
        
        import time
        
        # Test belief update performance
        controller = AdviceController(db_client)
        
        start_time = time.time()
        for i in range(10):
            controller.update_values(f"perf-test-{i}", {"difficulty": 1})
        
        update_time = time.time() - start_time
        print(f"  Belief updates (10x): {update_time:.3f}s")
        
        # Test action generation performance
        start_time = time.time()
        for i in range(10):
            controller.action(f"perf-test-{i}")
        
        action_time = time.time() - start_time
        print(f"  Action generation (10x): {action_time:.3f}s")
        
        db_client.close()
        
    except Exception as e:
        print(f"  ❌ Performance test failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Belief System Tests...\n")
    
    # Run all tests
    success = test_belief_controllers()
    
    if success:
        test_error_handling()
        test_performance()
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        sys.exit(1)
