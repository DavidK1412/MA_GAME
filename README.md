# 🐸 Frog Game - Sistema de Juego Educativo Inteligente

Un sistema de juego educativo que implementa el clásico **juego de las ranas** con inteligencia artificial adaptativa que proporciona retroalimentación personalizada al jugador.

## 🎯 Características Principales

- **Juego de las ranas** con 3 niveles de dificultad (7, 9, 11 bloques)
- **Sistema de IA adaptativa** que evalúa el comportamiento del jugador
- **5 tipos de ayuda inteligente** basados en métricas de rendimiento
- **API RESTful** construida con FastAPI
- **Base de datos PostgreSQL** con transacciones atómicas
- **Sistema de logging** profesional con rotación de archivos
- **Arquitectura modular** y fácilmente extensible

## 🏗️ Arquitectura del Sistema

```
MA_GAME/
├── app/                          # Código principal de la aplicación
│   ├── config/                   # Configuración del sistema
│   ├── core/                     # Funcionalidades core (excepciones, logging)
│   ├── controllers/              # Controladores de la lógica de negocio
│   │   ├── beliefs/             # Controladores del sistema de creencias
│   │   └── base.py              # Controlador base con funcionalidades comunes
│   ├── domain/                   # Modelos de dominio y entidades
│   ├── services/                 # Servicios de la aplicación
│   ├── utils/                    # Utilidades y helpers
│   └── main.py                   # Aplicación principal FastAPI
├── db/                          # Base de datos y migraciones
│   ├── migrations/              # Scripts de migración
│   └── seeds/                   # Datos iniciales
└── tests/                       # Tests automatizados
```

## 🧠 Sistema de Inteligencia Adaptativa

El sistema implementa un **sistema de creencias (beliefs)** que evalúa múltiples factores del jugador:

| Métrica | Descripción | Fórmula |
|---------|-------------|---------|
| **E** | Cantidad de errores | - |
| **B** | Buclicidad (movimientos repetitivos) | - |
| **IP** | Intentos por partida | - |
| **R** | Ramificación (diversidad de movimientos) | - |
| **CE** | Conocimiento de las reglas | - |
| **TPM** | Tiempo por movimiento | - |
| **TP** | Tiempo promedio | - |

### Tipos de Ayuda Disponibles

1. **Feedback** - Retroalimentación motivacional
2. **Advice** - Consejos y sugerencias
3. **Explain** - Explicaciones de reglas
4. **Demonstrate** - Demostraciones visuales
5. **Ask** - Preguntas para evaluar comprensión

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.8+
- PostgreSQL 12+
- pip

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd MA_GAME
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos

```bash
# Crear base de datos
createdb frog_game

# Ejecutar migraciones
psql -d frog_game -f db/migrations/001_initial_schema.sql
```

### 5. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar .env con tus credenciales
nano .env
```

### 6. Ejecutar la Aplicación

```bash
# Desarrollo
uvicorn app.main:app --reload

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 Uso de la API

### Endpoints Principales

#### Crear Nuevo Juego
```http
POST /game
Content-Type: application/json

{
  "game_id": "uuid-string"
}
```

#### Realizar Movimiento
```http
POST /game/{game_id}
Content-Type: application/json

{
  "movement": [1, 2, 3, 0, 4, 5, 6]
}
```

#### Registrar Error
```http
POST /game/{game_id}/miss
```

#### Obtener Mejor Movimiento
```http
GET /game/{game_id}/best_next
```

### Ejemplo de Uso con cURL

```bash
# Crear juego
curl -X POST "http://localhost:8000/game" \
  -H "Content-Type: application/json" \
  -d '{"game_id": "test-game-123"}'

# Realizar movimiento
curl -X POST "http://localhost:8000/game/test-game-123" \
  -H "Content-Type: application/json" \
  -d '{"movement": [1, 2, 3, 0, 4, 5, 6]}'
```

## 🔧 Desarrollo

### Estructura del Código

El proyecto sigue principios de **Clean Architecture** y **SOLID**:

- **Separación de responsabilidades** clara entre capas
- **Inyección de dependencias** para testing
- **Manejo de errores** robusto con excepciones personalizadas
- **Logging** estructurado para debugging y monitoreo
- **Validación de datos** con Pydantic

### Agregar Nuevo Controlador de Creencia

```python
from app.controllers.base import BeliefController

class NewBeliefController(BeliefController):
    def update_values(self, game_id: str, config: dict) -> bool:
        # Implementar lógica para actualizar valores
        pass
    
    def action(self, game_id: str):
        # Implementar acción de la creencia
        pass
```

### Ejecutar Tests

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio

# Ejecutar tests
pytest tests/
```

## 📊 Monitoreo y Logging

El sistema incluye logging estructurado con:

- **Rotación automática** de archivos de log
- **Diferentes niveles** de logging (DEBUG, INFO, WARNING, ERROR)
- **Formato estructurado** para fácil parsing
- **Logs separados** por consola y archivo

### Ejemplo de Log

```
2024-01-15 10:30:45 - INFO - Operation: game_created - Details: {'game_id': 'test-123'}
2024-01-15 10:30:46 - DEBUG - Query executed successfully: INSERT INTO game...
```

## 🐳 Docker

### Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PGHOST=db
      - PGDATABASE=frog_game
      - PGUSER=postgres
      - PGPASSWORD=password
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=frog_game
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes preguntas o problemas:

- Abre un issue en GitHub
- Contacta al equipo de desarrollo
- Revisa la documentación de la API en `/docs` (Swagger UI)

## 🔮 Roadmap

- [ ] Frontend web con React/Vue
- [ ] Sistema de usuarios y autenticación
- [ ] Métricas avanzadas de rendimiento
- [ ] Integración con sistemas de aprendizaje
- [ ] API para análisis de datos
- [ ] Tests de integración completos
- [ ] CI/CD pipeline
- [ ] Monitoreo con Prometheus/Grafana

---

**¡Disfruta jugando y aprendiendo con el sistema de ranas inteligente! 🐸✨**
