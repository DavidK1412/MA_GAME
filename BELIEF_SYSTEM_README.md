# 🧠 Sistema de Beliefs - Juego de Ranas

## Descripción General

El sistema de beliefs es el núcleo de la inteligencia artificial adaptativa del juego. Consiste en 5 agentes especializados que evalúan el comportamiento del jugador y proporcionan intervenciones personalizadas para mejorar la experiencia de aprendizaje.

## 🏗️ Arquitectura del Sistema

### Estructura de Clases

```
BeliefController (Abstract Base)
├── AdviceController
├── FeedbackController
├── ExplainController
├── DemonstrateController
└── AskController
```

### Flujo de Funcionamiento

1. **Evaluación**: Cada controller evalúa métricas del jugador
2. **Cálculo de Belief**: Se calcula un valor entre 0.0 y 1.0
3. **Selección**: El DecisionController selecciona el mejor belief
4. **Acción**: Se ejecuta la acción correspondiente

## 🎯 Controllers Implementados

### 1. AdviceController
**Propósito**: Proporcionar consejos estratégicos y ajustar dificultad

**Métricas Evaluadas**:
- `IP` (Intentos por juego)
- `R` (Factor de ramificación)

**Acciones**:
- Mensajes de motivación
- Reducción de dificultad
- Creación de nuevos intentos

**Código Clave**:
```python
def update_values(self, game_id: str, config: Dict[str, Any]) -> bool:
    metrics = get_game_progress(game_id, self.db_client)
    
    # Factor 1: High tries count
    if metrics['tries_count'] > 15:
        belief_value += 0.4
    elif metrics['tries_count'] > 10:
        belief_value += 0.3
```

### 2. FeedbackController
**Propósito**: Proporcionar feedback personalizado basado en rendimiento

**Métricas Evaluadas**:
- Rendimiento general (30%)
- Progreso de aprendizaje (25%)
- Nivel de engagement (20%)
- Adaptación a dificultad (25%)

**Acciones**:
- Feedback específico por nivel de rendimiento
- Análisis de patrones de juego
- Sugerencias de mejora

### 3. ExplainController
**Propósito**: Explicar reglas y conceptos del juego

**Métricas Evaluadas**:
- Número de intentos
- Errores cometidos
- Buclicity (patrones repetitivos)
- Nivel de habilidad

**Acciones**:
- Explicaciones detalladas de reglas
- Recordatorios contextuales
- Validación de comprensión

### 4. DemonstrateController
**Propósito**: Mostrar movimientos óptimos y estrategias

**Métricas Evaluadas**:
- Necesidad de demostración
- Estado actual del juego
- Viabilidad de la posición

**Acciones**:
- Movimientos óptimos
- Pistas estratégicas
- Análisis de posiciones

### 5. AskController
**Propósito**: Hacer preguntas interactivas para evaluar comprensión

**Métricas Evaluadas**:
- Nivel de engagement
- Tiempo entre movimientos
- Comprensión del juego

**Acciones**:
- Preguntas estratégicas
- Evaluación de comprensión
- Preguntas de seguimiento

## 📊 Sistema de Métricas

### Métricas Principales

| Métrica | Descripción | Rango |
|---------|-------------|-------|
| `tries_count` | Número de intentos | 0+ |
| `misses_count` | Errores cometidos | 0+ |
| `buclicity` | Patrones repetitivos | 0+ |
| `branch_factor` | Diversidad de movimientos | 1.0+ |
| `repeated_states` | Estados repetidos | 0+ |
| `average_time` | Tiempo promedio entre movimientos | 0+ |
| `correct_moves` | Movimientos correctos | 0+ |

### Cálculo de Nivel de Habilidad

```python
def calculate_player_skill_level(game_id: str, db_client) -> float:
    metrics = get_game_progress(game_id, db_client)
    
    # Normalización y ponderación
    tries_score = max(0, 1 - (metrics['tries_count'] / 20))
    misses_score = max(0, 1 - (metrics['misses_count'] / 10))
    buclicity_score = max(0, 1 - (metrics['buclicity'] / 10))
    # ... más factores
    
    return weighted_average
```

## 🔧 Integración con Graph Utils

### Funciones Utilizadas

- `possible_moves()`: Genera movimientos válidos
- `shortest_path_length()`: Calcula distancia al objetivo
- `best_next_move()`: Encuentra el mejor movimiento
- `is_game_winnable()`: Verifica si el juego es resoluble

### Manejo de Errores

```python
try:
    optimal_move = best_next_move(current_state, final_state)
    if optimal_move is None:
        return "No se pudo encontrar un movimiento óptimo"
except Exception as e:
    logger.error(f"Error calculating optimal move: {e}")
    return "Error al calcular el movimiento"
```

## 🗄️ Base de Datos

### Campos de Belief

```sql
ALTER TABLE game_attempts 
ADD COLUMN advice_belief DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN feedback_belief DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN explain_belief DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN demonstrate_belief DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN ask_belief DECIMAL(3,2) DEFAULT 0.00;
```

### Índices de Rendimiento

```sql
CREATE INDEX idx_game_attempts_advice_belief ON game_attempts(advice_belief);
CREATE INDEX idx_game_attempts_active_beliefs ON game_attempts(is_active, advice_belief, feedback_belief, explain_belief, demonstrate_belief, ask_belief);
```

## 🧪 Testing

### Script de Prueba

```bash
python app/tests/test_belief_system.py
```

### Pruebas Incluidas

1. **Funcionalidad**: Verifica que todos los controllers funcionen
2. **Manejo de Errores**: Prueba casos edge y errores
3. **Rendimiento**: Mide tiempos de respuesta
4. **Integración**: Verifica la integración con graph_utils

## 🚀 Uso del Sistema

### Inicialización

```python
from app.controllers.beliefs.advice import AdviceController
from app.utils.database import DatabaseClient

db_client = DatabaseClient()
db_client.connect()

advice_controller = AdviceController(db_client)
```

### Evaluación de Beliefs

```python
# Actualizar valores de belief
success = advice_controller.update_values(game_id, config)

# Obtener acción
response = advice_controller.action(game_id)
print(f"Message: {response.message}")
print(f"Belief Value: {response.belief_value}")
```

### Selección del Mejor Belief

```python
from app.controllers.decision import DecisionController

decision_controller = DecisionController(db_client)
best_belief = decision_controller.select_best_belief(game_id, config)

if best_belief:
    print(f"Best belief: {best_belief['name']}")
    print(f"Value: {best_belief['value']}")
```

## 📈 Monitoreo y Logging

### Sistema de Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Belief value updated: {belief_value}")
logger.warning(f"High buclicity detected: {metrics['buclicity']}")
logger.error(f"Error in belief calculation: {e}")
```

### Métricas de Rendimiento

- Tiempo de actualización de beliefs
- Tiempo de generación de acciones
- Tasa de éxito de operaciones
- Uso de memoria y CPU

## 🔮 Mejoras Futuras

### Funcionalidades Planificadas

1. **Machine Learning**: Entrenamiento de modelos para mejor predicción
2. **Personalización**: Adaptación individual por jugador
3. **A/B Testing**: Comparación de diferentes estrategias
4. **Analytics**: Dashboard de métricas y insights

### Optimizaciones Técnicas

1. **Caching**: Cache de cálculos de belief
2. **Async Processing**: Procesamiento asíncrono de métricas
3. **Batch Updates**: Actualizaciones en lote de beliefs
4. **Real-time Updates**: Actualizaciones en tiempo real

## 🐛 Troubleshooting

### Problemas Comunes

1. **Belief Values Always 0**
   - Verificar conexión a base de datos
   - Revisar métricas calculadas
   - Verificar logs de error

2. **Graph Utils Errors**
   - Validar estados del juego
   - Verificar parámetros de dificultad
   - Revisar límites de iteración

3. **Performance Issues**
   - Verificar índices de base de datos
   - Revisar consultas SQL
   - Monitorear uso de recursos

### Debugging

```python
# Habilitar logging detallado
import logging
logging.basicConfig(level=logging.DEBUG)

# Verificar métricas
metrics = get_game_progress(game_id, db_client)
print(f"Metrics: {metrics}")

# Verificar belief values
query = "SELECT * FROM game_attempts WHERE game_id = %s"
result = db_client.fetch_results(query, (game_id,))
print(f"Database state: {result}")
```

## 📚 Referencias

- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [NetworkX Documentation](https://networkx.org/)

---

**Nota**: Este sistema está diseñado para ser extensible y mantenible. Cualquier nueva funcionalidad debe seguir los principios de Clean Architecture y mantener la consistencia con el sistema existente.
