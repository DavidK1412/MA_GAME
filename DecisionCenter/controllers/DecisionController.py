from utils import DatabaseClient


class DecisionController:
    def __init__(self, beliefs: list, config: dict):
        self.beliefs = beliefs
        self.config = config

    def evaluate_beliefs(self, game_id: str):
        evaluated_beliefs: list = []
        print("Length of beliefs: ", len(self.beliefs))
        for belief in self.beliefs:
            evaluated_beliefs.append({
                'belief': belief,
                'value': belief.evaluate_belief(game_id, self.config)
            })
        print(evaluated_beliefs)
        
        return max(evaluated_beliefs, key=lambda x: x['value'])['belief'] if evaluated_beliefs else None

    def make_decision(self, game_id: str):
        belief = self.evaluate_beliefs(game_id)
        if not belief:
            raise ValueError('No beliefs found')
        return belief