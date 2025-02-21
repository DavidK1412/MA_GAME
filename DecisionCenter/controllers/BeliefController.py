from utils import DatabaseClient, evaluate_equation, replace_placeholders_in_equation

class BeliefController:
    def __init__(self, dn_client: DatabaseClient, name: str):
        self.db_client = dn_client
        self.values = None
        self.name = name

    def evaluate_belief(self, game_id: str ,config: dict) -> float:
        if not self.update_values(game_id, config):
            raise ValueError(f'Error updating values for belief {self.name}')
        belief = config['beliefs'].get(self.name)
        if not belief:
            raise ValueError(f'Belief {self.name} not found in config')
        equation = belief.get('Equation')
        weights = belief.get('Weights')
        standardization = belief.get('Standardization', {})

        normalized_values = {}
        print(standardization)
        for var, value in self.values.items():
            max_value = standardization.get(f"{var}_max", 1)  # Default: sin normalización
            print(f"{var}_max", max_value)
            print(value)
            normalized_values[var] = value / max_value
        print (normalized_values)
        context = {**weights, **normalized_values}
        processed_equation = replace_placeholders_in_equation(equation, context)
        print(processed_equation)
        
        return evaluate_equation(processed_equation, context)
    
    def update_values(self, game_id: str, config: dict):
        pass
