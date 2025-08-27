"""
Decision controller for managing belief system decisions.
"""

from typing import List, Dict, Any, Optional
from controllers.base import BaseController
from core.exceptions import BeliefEvaluationError
from core.logging import get_logger


class DecisionController(BaseController):
    """Controller for making decisions based on belief evaluations."""
    
    def __init__(self, beliefs: List, config: Dict[str, Any]):
        super().__init__(None, "DecisionController")
        self.beliefs = beliefs
        self.config = config
        self.logger = get_logger(__name__)

    def evaluate_beliefs(self, game_id: str) -> List[Dict[str, Any]]:
        """Evaluate all beliefs for a specific game."""
        try:
            evaluated_beliefs = []
            self.logger.info(f"Evaluating {len(self.beliefs)} beliefs for game {game_id}")
            
            for belief in self.beliefs:
                try:
                    value = belief.evaluate_belief(game_id, self.config)
                    evaluated_beliefs.append({
                        'belief': belief,
                        'value': value,
                        'name': belief.name
                    })
                    self.logger.debug(f"Belief {belief.name} evaluated: {value}")
                except Exception as e:
                    self.logger.error(f"Error evaluating belief {belief.name}: {e}")
                    # Continue with other beliefs instead of failing completely
                    continue
            
            if not evaluated_beliefs:
                raise BeliefEvaluationError("No beliefs could be evaluated successfully")
            
            # Log consolidado de valores por creencia
            try:
                resumen = ", ".join([f"{b['name']}={b['value']:.4f}" for b in evaluated_beliefs])
                self.logger.info(f"Valores de creencias para juego {game_id}: {resumen}")
            except Exception:
                # Fallback en caso de tipos no numéricos
                self.logger.info({
                    "game_id": game_id,
                    "belief_values": [{"name": b.get('name'), "value": b.get('value')} for b in evaluated_beliefs]
                })

            self.logger.info(f"Successfully evaluated {len(evaluated_beliefs)} beliefs")
            return evaluated_beliefs
            
        except Exception as e:
            self.logger.error(f"Error in belief evaluation: {e}")
            raise BeliefEvaluationError(f"Failed to evaluate beliefs: {e}")

    def make_decision(self, game_id: str):
        """Make a decision based on belief evaluations."""
        try:
            evaluated_beliefs = self.evaluate_beliefs(game_id)
            
            if not evaluated_beliefs:
                raise BeliefEvaluationError("No beliefs available for decision making")
            
            # Tie-break priority: Demonstrate > Ask > Explain > Advice > Feedback
            priority = {
                'Demonstrate': 0,
                'Ask': 1,
                'Explain': 2,
                'Advice': 3,
                'Feedback': 4,
            }
            # Select belief with highest value; on tie, use priority
            best_belief = min(
                evaluated_beliefs,
                key=lambda x: (-float(x['value']), priority.get(x['name'], 99))
            )
            
            self.logger.info(f"Selected belief {best_belief['name']} with value {best_belief['value']}")
            # Log explícito del ganador (para debug claro en español)
            try:
                self.logger.info(
                    {
                        "event": "belief_winner",
                        "game_id": game_id,
                        "winner": best_belief['name'],
                        "value": float(best_belief['value'])
                    }
                )
            except Exception:
                self.logger.info(f"Belief winner: {best_belief['name']} (value={best_belief['value']})")
            
            return best_belief['belief']
            
        except Exception as e:
            self.logger.error(f"Error making decision: {e}")
            raise BeliefEvaluationError(f"Failed to make decision: {e}")

    def get_belief_ranking(self, game_id: str) -> List[Dict[str, Any]]:
        """Get a ranking of all beliefs for a game."""
        try:
            evaluated_beliefs = self.evaluate_beliefs(game_id)
            
            # Sort by value desc with tie-break priority
            priority = {
                'Demonstrate': 0,
                'Ask': 1,
                'Explain': 2,
                'Advice': 3,
                'Feedback': 4,
            }
            ranked_beliefs = sorted(
                evaluated_beliefs,
                key=lambda x: (-float(x['value']), priority.get(x['name'], 99))
            )
            
            self.logger.info(f"Belief ranking generated for game {game_id}")
            return ranked_beliefs
            
        except Exception as e:
            self.logger.error(f"Error generating belief ranking: {e}")
            raise BeliefEvaluationError(f"Failed to generate belief ranking: {e}")

    def get_belief_statistics(self, game_id: str) -> Dict[str, Any]:
        """Get statistics about belief evaluations."""
        try:
            evaluated_beliefs = self.evaluate_beliefs(game_id)
            
            if not evaluated_beliefs:
                return {}
            
            values = [belief['value'] for belief in evaluated_beliefs]
            
            stats = {
                'total_beliefs': len(evaluated_beliefs),
                'highest_value': max(values),
                'lowest_value': min(values),
                'average_value': sum(values) / len(values),
                'beliefs_evaluated': [belief['name'] for belief in evaluated_beliefs]
            }
            
            self.logger.info(f"Statistics generated for game {game_id}: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error generating belief statistics: {e}")
            raise BeliefEvaluationError(f"Failed to generate belief statistics: {e}")
