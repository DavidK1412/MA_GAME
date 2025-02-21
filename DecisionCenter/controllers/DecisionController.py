from utils import DatabaseClient


class DecisionController:
    def __init__(self, beliefs: list, config: dict):
        self.beliefs = beliefs
        self.config = config

    def evaluate_beliefs(self, game_id: str) -> dict:
        evaluated_beliefs: list = []
        for belief in self.beliefs:
            evaluated_beliefs.append({
                'name': belief.name,
                'value': belief.evaluate_belief(game_id, self.config)
            })
        
        return max(evaluated_beliefs, key=lambda x: x['value']) if evaluated_beliefs else None

    def make_decision(self, game_id: str) -> dict:
        belief = self.evaluate_beliefs(game_id)
        if not belief:
            raise ValueError('No beliefs found')
        return belief