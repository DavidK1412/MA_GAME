"""
Demonstrate belief controller for showing players how to solve game situations.
"""

from typing import Any, Dict, List, Optional
from controllers.base import BeliefController
from domain.models.response import SpeechResponse, GameResponse, Response, ResponseType
from utils.incentive_scripts import get_game_progress, calculate_player_skill_level
from utils.graph_utils import best_next_move, possible_moves, is_game_winnable


class DemonstrateController(BeliefController):
    """
    Demonstrate belief controller that shows players optimal moves and strategies.
    """
    
    def __init__(self, db_client, name: str = "Demonstrate"):
        super().__init__(db_client, name)
    
    def update_values(self, game_id: str, config: Dict[str, Any]) -> bool:
        """
        Update belief values based on player's need for demonstration.
        
        Args:
            game_id: Game identifier
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get game progress metrics
            metrics = get_game_progress(game_id, self.db_client)
            
            # Calculate belief value based on demonstration needs
            belief_value = 0.0
            
            # Factor 1: High tries count suggests need for demonstration
            if metrics['tries_count'] > 20:
                belief_value += 0.4
            elif metrics['tries_count'] > 15:
                belief_value += 0.3
            elif metrics['tries_count'] > 10:
                belief_value += 0.2
            
            # Factor 2: High misses indicate need to see correct moves
            if metrics['misses_count'] > 8:
                belief_value += 0.3
            elif metrics['misses_count'] > 5:
                belief_value += 0.2
            
            # Factor 3: High buclicity suggests getting stuck in patterns
            if metrics['buclicity'] > 7:
                belief_value += 0.2
            
            # Factor 4: Low skill level needs more guidance
            skill_level = calculate_player_skill_level(game_id, self.db_client)
            if skill_level < 0.2:
                belief_value += 0.3
            elif skill_level < 0.4:
                belief_value += 0.2
            
            # Factor 5: Check if game is winnable from current state
            if not self._is_current_state_winnable(game_id):
                belief_value += 0.2
            
            # Cap belief value at 1.0 (sin escribir en BD)
            belief_value = min(1.0, belief_value)
            self.values = {"belief_value": belief_value, **metrics}
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating demonstrate belief values: {e}")
            return False
    
    def _is_current_state_winnable(self, game_id: str) -> bool:
        """Check if the current game state is winnable."""
        try:
            # Get current game state and difficulty
            query = """
                SELECT ga.difficulty_id, m.movement, ga.id
                FROM game_attempts ga
                JOIN movements m ON ga.id = m.attempt_id
                WHERE ga.game_id = %s AND ga.is_active = TRUE
                ORDER BY m.step DESC
                LIMIT 1
            """
            params = (game_id,)
            result = self.db_client.fetch_results(query, params)
            
            if not result:
                return False
            
            difficulty_id = result[0]['difficulty_id']
            current_state_str = result[0]['movement']
            
            # Parse current state
            try:
                current_state = [int(x.strip()) for x in current_state_str.split(",") if x.strip()]
            except (ValueError, AttributeError):
                return False
            
            # Get difficulty configuration
            difficulty_configs = {
                1: {"blocks_per_team": 3, "final_state": [6, 5, 4, 0, 1, 2, 3]},
                2: {"blocks_per_team": 4, "final_state": [8, 7, 6, 5, 0, 1, 2, 3, 4]},
                3: {"blocks_per_team": 5, "final_state": [10, 9, 8, 7, 6, 0, 1, 2, 3, 4, 5]}
            }
            
            if difficulty_id not in difficulty_configs:
                return False
            
            difficulty = difficulty_configs[difficulty_id]
            blocks_per_team = difficulty['blocks_per_team']
            final_state = difficulty['final_state']
            
            # Check if current state is winnable (usar firma de 2 argumentos)
            return is_game_winnable(current_state, final_state)
            
        except Exception as e:
            self.logger.error(f"Error checking if state is winnable: {e}")
            return False
    
    def action(self, game_id: str) -> SpeechResponse:
        """
        Provide demonstration action based on belief evaluation.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Response BEST_NEXT cuando sea posible, o SPEECH como fallback
        """
        try:
            # Recalcular belief_value en memoria y obtener dificultad (sin columnas de creencias)
            metrics = get_game_progress(game_id, self.db_client)
            belief_value = 0.0
            if metrics['tries_count'] > 20:
                belief_value += 0.4
            elif metrics['tries_count'] > 15:
                belief_value += 0.3
            elif metrics['tries_count'] > 10:
                belief_value += 0.2
            if metrics['misses_count'] > 8:
                belief_value += 0.3
            elif metrics['misses_count'] > 5:
                belief_value += 0.2
            if metrics['buclicity'] > 7:
                belief_value += 0.2
            skill_level = calculate_player_skill_level(game_id, self.db_client)
            if skill_level < 0.2:
                belief_value += 0.3
            elif skill_level < 0.4:
                belief_value += 0.2
            if not self._is_current_state_winnable(game_id):
                belief_value += 0.2
            belief_value = min(1.0, belief_value)

            difficulty_id = 1
            try:
                res = self.db_client.fetch_results(
                    "SELECT difficulty_id FROM game_attempts WHERE game_id = %s AND is_active = TRUE",
                    (game_id,)
                )
                if res:
                    difficulty_id = int(res[0].get('difficulty_id', 1))
            except Exception:
                difficulty_id = 1
            
            # Get current game state
            current_state = self._get_current_game_state(game_id)
            if not current_state:
                return SpeechResponse.create_encouragement(
                    "No se pudo obtener el estado actual del juego."
                )
            
            # Intentar devolver siempre el mejor siguiente movimiento como BEST_NEXT
            difficulty_configs = {
                1: {"blocks_per_team": 3, "final_state": [6, 5, 4, 0, 1, 2, 3]},
                2: {"blocks_per_team": 4, "final_state": [8, 7, 6, 5, 0, 1, 2, 3, 4]},
                3: {"blocks_per_team": 5, "final_state": [10, 9, 8, 7, 6, 0, 1, 2, 3, 4, 5]}
            }
            final_state = difficulty_configs.get(difficulty_id, {}).get('final_state')
            if final_state:
                optimal_move = best_next_move(current_state, final_state)
                if optimal_move is not None:
                    return Response(
                        type=ResponseType.BEST_NEXT,
                        actions={
                            "text": "Este es el movimiento correcto",
                            "best_next": optimal_move
                        }
                    )

            # Fallback: mensaje explicativo
            message = self._generate_demonstration_message(
                belief_value, current_state, difficulty_id, game_id
            )
            return SpeechResponse.create_encouragement(message)
            
        except Exception as e:
            self.logger.error(f"Error in demonstrate action: {e}")
            return SpeechResponse.create_encouragement(
                "Ocurrió un error al generar la demostración."
            )
    
    def _get_current_game_state(self, game_id: str) -> Optional[List[int]]:
        """Get the current game state as a list of integers."""
        try:
            query = """
                SELECT m.movement
                FROM game_attempts ga
                JOIN movements m ON ga.id = m.attempt_id
                WHERE ga.game_id = %s AND ga.is_active = TRUE
                ORDER BY m.step DESC
                LIMIT 1
            """
            params = (game_id,)
            result = self.db_client.fetch_results(query, params)
            
            if not result:
                return None
            
            state_str = result[0]['movement']
            return [int(x.strip()) for x in state_str.split(",") if x.strip()]
            
        except Exception as e:
            self.logger.error(f"Error getting current game state: {e}")
            return None
    
    def _generate_demonstration_message(
        self, 
        belief_value: float, 
        current_state: List[int], 
        difficulty_id: int, 
        game_id: str
    ) -> str:
        """Generate demonstration message based on belief value and game state."""
        
        if belief_value >= 0.7:
            # High need for demonstration - show optimal next move
            return self._show_optimal_move(current_state, difficulty_id, game_id)
        
        elif belief_value >= 0.5:
            # Moderate need - show possible moves
            return self._show_possible_moves(current_state, difficulty_id)
        
        elif belief_value >= 0.3:
            # Low need - provide strategic hints
            return self._provide_strategic_hint(current_state, difficulty_id)
        
        else:
            # Very low need - just encouragement
            return (
                "¡Excelente! Estás resolviendo el juego de manera independiente. "
                "Continúa así y pronto completarás el nivel sin ayuda."
            )
    
    def _show_optimal_move(self, current_state: List[int], difficulty_id: int, game_id: str) -> str:
        """Show the optimal next move for the player."""
        try:
            # Get difficulty configuration
            difficulty_configs = {
                1: {"blocks_per_team": 3, "final_state": [6, 5, 4, 0, 1, 2, 3]},
                2: {"blocks_per_team": 4, "final_state": [8, 7, 6, 5, 0, 1, 2, 3, 4]},
                3: {"blocks_per_team": 5, "final_state": [10, 9, 8, 7, 6, 0, 1, 2, 3, 4, 5]}
            }
            
            if difficulty_id not in difficulty_configs:
                return "No se pudo determinar la configuración de dificultad."
            
            difficulty = difficulty_configs[difficulty_id]
            blocks_per_team = difficulty['blocks_per_team']
            final_state = difficulty['final_state']
            
            # Get optimal next move
            optimal_move = best_next_move(current_state, final_state)
            
            if optimal_move is None:
                return (
                    "No se pudo encontrar un movimiento óptimo desde tu posición actual. "
                    "Intenta revisar las reglas del juego o considera reiniciar el nivel."
                )
            
            # Find which frog moved
            moved_frog = self._find_moved_frog(current_state, optimal_move)
            
            if moved_frog is None:
                return (
                    "Te sugiero el siguiente movimiento óptimo: "
                    f"mueve una rana desde la posición {current_state} "
                    f"hacia {optimal_move}. "
                    "Recuerda: solo puedes mover hacia adelante."
                )
            
            return (
                f"Te muestro el mejor movimiento: mueve la rana en la posición {moved_frog}. "
                f"Esto te llevará de {current_state} a {optimal_move}. "
                "Este movimiento te acerca más a la solución óptima del juego."
            )
            
        except Exception as e:
            self.logger.error(f"Error showing optimal move: {e}")
            return "Ocurrió un error al calcular el movimiento óptimo."
    
    def _show_possible_moves(self, current_state: List[int], difficulty_id: int) -> str:
        """Show possible moves without revealing the optimal one."""
        try:
            difficulty_configs = {
                1: {"blocks_per_team": 3},
                2: {"blocks_per_team": 4},
                3: {"blocks_per_team": 5}
            }
            
            if difficulty_id not in difficulty_configs:
                return "No se pudo determinar la configuración de dificultad."
            
            blocks_per_team = difficulty_configs[difficulty_id]['blocks_per_team']
            
            # Get possible moves
            possible_moves_list = possible_moves(blocks_per_team, blocks_per_team, current_state)
            
            if not possible_moves_list:
                return "No hay movimientos válidos desde tu posición actual."
            
            # Count valid moves
            valid_moves_count = len(possible_moves_list)
            
            return (
                f"Desde tu posición actual tienes {valid_moves_count} movimientos válidos. "
                "Recuerda las reglas: las ranas solo pueden saltar hacia adelante, "
                "una casilla o sobre otra rana. "
                "Elige el que te parezca más prometedor."
            )
            
        except Exception as e:
            self.logger.error(f"Error showing possible moves: {e}")
            return "Ocurrió un error al calcular los movimientos posibles."
    
    def _provide_strategic_hint(self, current_state: List[int], difficulty_id: int) -> str:
        """Provide strategic hints without showing specific moves."""
        try:
            # Analyze current state for strategic insights
            left_frogs = [i for i, val in enumerate(current_state) if val > 0]
            right_frogs = [i for i, val in enumerate(current_state) if val < 0]
            
            if not left_frogs or not right_frogs:
                return "Tu posición actual parece estar cerca del objetivo. ¡Sigue así!"
            
            # Check if frogs are blocked
            blocked_frogs = self._count_blocked_frogs(current_state)
            
            if blocked_frogs > 0:
                return (
                    f"Tienes {blocked_frogs} ranas bloqueadas. "
                    "Intenta liberar espacio moviendo las ranas que están en el extremo. "
                    "A veces, dar un paso atrás te ayuda a avanzar."
                )
            
            # Check for optimal positioning
            if self._is_good_positioning(current_state, difficulty_id):
                return (
                    "Tu posición actual es estratégicamente buena. "
                    "Las ranas están bien distribuidas. "
                    "Continúa con movimientos que mantengan esta estructura."
                )
            else:
                return (
                    "Considera reorganizar las ranas para crear una mejor estructura. "
                    "A veces, mover una rana que parece no importante "
                    "puede abrir nuevas posibilidades."
                )
                
        except Exception as e:
            self.logger.error(f"Error providing strategic hint: {e}")
            return "Ocurrió un error al generar la pista estratégica."
    
    def _find_moved_frog(self, old_state: List[int], new_state: List[int]) -> Optional[int]:
        """Find which frog moved between two states."""
        if len(old_state) != len(new_state):
            return None
        
        for i, (old_val, new_val) in enumerate(zip(old_state, new_state)):
            if old_val != new_val:
                return i
        
        return None
    
    def _count_blocked_frogs(self, state: List[int]) -> int:
        """Count how many frogs are blocked from moving."""
        blocked_count = 0
        
        for i, val in enumerate(state):
            if val == 0:  # Empty space
                continue
            
            if val > 0:  # Left frog
                # Check if frog can move right
                if i + 1 < len(state) and state[i + 1] == 0:
                    continue
                if i + 2 < len(state) and state[i + 1] != 0 and state[i + 2] == 0:
                    continue
                blocked_count += 1
            
            elif val < 0:  # Right frog
                # Check if frog can move left
                if i - 1 >= 0 and state[i - 1] == 0:
                    continue
                if i - 2 >= 0 and state[i - 1] != 0 and state[i - 2] == 0:
                    continue
                blocked_count += 1
        
        return blocked_count
    
    def _is_good_positioning(self, state: List[int], difficulty_id: int) -> bool:
        """Check if the current positioning is strategically good."""
        try:
            # Simple heuristic: check if frogs are not too clustered
            left_frogs = [i for i, val in enumerate(state) if val > 0]
            right_frogs = [i for i, val in enumerate(state) if val < 0]
            
            if not left_frogs or not right_frogs:
                return True
            
            # Check spacing between frogs
            left_spacing = self._calculate_spacing(left_frogs)
            right_spacing = self._calculate_spacing(right_frogs)
            
            # Good positioning if frogs have reasonable spacing
            return left_spacing >= 1 and right_spacing >= 1
            
        except Exception:
            return False
    
    def _calculate_spacing(self, positions: List[int]) -> float:
        """Calculate average spacing between positions."""
        if len(positions) <= 1:
            return float('inf')
        
        total_spacing = 0
        for i in range(1, len(positions)):
            total_spacing += positions[i] - positions[i-1]
        
        return total_spacing / (len(positions) - 1)
