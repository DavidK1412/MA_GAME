"""
Base controller with common functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.logging import get_logger
from utils.database import DatabaseClient


class BaseController(ABC):
    """Base controller class with common functionality."""
    
    def __init__(self, db_client: DatabaseClient, name: str):
        self.db_client = db_client
        self.name = name
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log an operation with optional details."""
        message = f"Operation: {operation}"
        if details:
            message += f" - Details: {details}"
        self.logger.info(message)
    
    def log_error(self, operation: str, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with operation and details."""
        message = f"Error in operation: {operation} - {str(error)}"
        if details:
            message += f" - Details: {details}"
        self.logger.error(message, exc_info=True)
    
    def validate_database_connection(self) -> bool:
        """Validate that database connection is active."""
        if not self.db_client.is_connected():
            self.logger.warning("Database connection lost, attempting to reconnect...")
            try:
                self.db_client.connect()
                return True
            except Exception as e:
                self.log_error("database_reconnection", e)
                return False
        return True
    
    def safe_execute_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """Safely execute a database query with error handling."""
        try:
            self.validate_database_connection()
            # Ensure writes are committed by using an explicit transaction
            with self.db_client.transaction():
                self.db_client.execute_query(query, params)
            self.log_operation("database_query_executed", {"query": query[:100]})
            return True
        except Exception as e:
            self.log_error("database_query_execution", e, {"query": query[:100], "params": params})
            return False
    
    def safe_fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        """Safely fetch results from database with error handling."""
        try:
            self.validate_database_connection()
            results = self.db_client.fetch_results(query, params)
            self.log_operation("database_results_fetched", {"count": len(results)})
            return results
        except Exception as e:
            self.log_error("database_results_fetch", e, {"query": query[:100], "params": params})
            return []


class BeliefController(BaseController):
    """Base controller for belief system controllers."""
    
    def __init__(self, db_client: DatabaseClient, name: str):
        super().__init__(db_client, name)
        self.values: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def update_values(self, game_id: str, config: Dict[str, Any]) -> bool:
        """Update belief values for a specific game."""
        pass
    
    @abstractmethod
    def action(self, game_id: str) -> Any:
        """Execute the belief action for a specific game."""
        pass
    
    def evaluate_belief(self, game_id: str, config: Dict[str, Any]) -> float:
        """Evaluate belief based on current values and configuration."""
        try:
            if not self.update_values(game_id, config):
                raise ValueError(f'Error updating values for belief {self.name}')
            
            # Configuración de la creencia (tolerante si no existe 'agents')
            belief_config = None
            try:
                agents_cfg = config.get('agents') if isinstance(config, dict) else None
                if isinstance(agents_cfg, dict):
                    belief_config = agents_cfg.get(self.name)
            except Exception:
                belief_config = None
            
            equation = None
            if isinstance(belief_config, dict):
                equation = belief_config.get('Equation')
            
            # Import here to avoid circular imports
            from utils.equation_utils import evaluate_equation, replace_placeholders_in_equation
            
            weights = belief_config.get('Weights', {}) if isinstance(belief_config, dict) else {}
            standardization = belief_config.get('Standardization', {}) if isinstance(belief_config, dict) else {}
            
            # Normalize values
            normalized_values = {}
            for var, value in self.values.items():
                max_value = standardization.get(f"{var}_max", 1)
                normalized_values[var] = value / max_value if max_value > 0 else 0
            
            # Si no hay ecuación, usar fallback (promedio de valores normalizados)
            if not equation:
                result = sum(normalized_values.values()) / max(1, len(normalized_values))
                processed_equation = "fallback_average_normalized_values"
                self.log_operation("belief_evaluated_fallback", {
                    "belief": self.name,
                    "normalized_values": normalized_values,
                    "result": result
                })
            else:
                context = {**weights, **normalized_values}
                processed_equation = replace_placeholders_in_equation(equation, context)
                result = evaluate_equation(processed_equation, context)
            # Log detallado de creencias: valores crudos, normalizados, pesos y resultado
            self.log_operation("belief_values", {
                "belief": self.name,
                "raw_values": self.values,
                "normalized_values": normalized_values,
                "weights": weights,
                "equation": equation,
                "processed_equation": processed_equation,
                "result": result
            })
            self.log_operation("belief_evaluated", {
                "belief": self.name,
                "values": self.values,
                "result": result
            })
            
            return result
            
        except Exception as e:
            self.log_error("belief_evaluation", e, {"game_id": game_id, "belief": self.name})
            raise
