# 🚀 Guía Paso a Paso - Colección de Postman para el Juego de Ranas

## 📋 **Prerrequisitos**

1. **Postman instalado** en tu computadora
2. **Servidor del juego ejecutándose** en `http://localhost:8000`
3. **Base de datos PostgreSQL** configurada y funcionando
4. **Dependencias del proyecto** instaladas

## 🔧 **Configuración Inicial**

### **1. Importar la Colección**
1. Abre Postman
2. Haz clic en "Import"
3. Selecciona el archivo `FROG_GAME_POSTMAN_COLLECTION.json`
4. La colección aparecerá en tu workspace

### **2. Configurar Variables de Entorno**
1. En la colección, haz clic en "Variables"
2. Verifica que `base_url` esté configurado como `http://localhost:8000`
3. Las variables `game_id` y `attempt_id` se llenarán automáticamente

## 🎮 **Flujo de Prueba Completo**

### **Paso 1: Verificar Salud de la API**
- **Request**: `🏠 Health Check`
- **Método**: GET
- **URL**: `{{base_url}}/`
- **Propósito**: Confirmar que la API esté funcionando
- **Respuesta Esperada**: Status 200 con mensaje de bienvenida

### **Paso 2: Crear Nuevo Juego**
- **Request**: `🎮 Crear Nuevo Juego`
- **Método**: POST
- **URL**: `{{base_url}}/game/create`
- **Body**:
```json
{
  "difficulty": 1
}
```
- **Propósito**: Crear un nuevo juego con dificultad 1
- **Respuesta Esperada**: Status 200 con `game_id`
- **Nota**: El `game_id` se guarda automáticamente en las variables

### **Paso 3: Iniciar Intento**
- **Request**: `🚀 Iniciar Intento`
- **Método**: POST
- **URL**: `{{base_url}}/game/start`
- **Body**:
```json
{
  "game_id": "{{game_id}}"
}
```
- **Propósito**: Iniciar un intento para el juego creado
- **Respuesta Esperada**: Status 200 con `attempt_id`

### **Paso 4: Verificar Estado del Juego**
- **Request**: `📊 Obtener Estado del Juego`
- **Método**: GET
- **URL**: `{{base_url}}/game/{{game_id}}/status`
- **Propósito**: Ver el estado actual del juego
- **Respuesta Esperada**: Estado inicial del juego

### **Paso 5: Realizar Primer Movimiento**
- **Request**: `🔄 Realizar Movimiento`
- **Método**: POST
- **URL**: `{{base_url}}/game/move`
- **Body**:
```json
{
  "game_id": "{{game_id}}",
  "movement": [3, 2, 1, 0, -1, -2, -3]
}
```
- **Propósito**: Realizar el primer movimiento válido
- **Respuesta Esperada**: Status 200 con confirmación del movimiento

### **Paso 6: Evaluar Beliefs del Sistema**
- **Request**: `🧠 Evaluar Beliefs`
- **Método**: POST
- **URL**: `{{base_url}}/beliefs/evaluate`
- **Body**:
```json
{
  "game_id": "{{game_id}}",
  "config": {
    "difficulty": 1,
    "max_tries": 20,
    "time_limit": 300
  }
}
```
- **Propósito**: Activar el sistema de beliefs para evaluar al jugador
- **Respuesta Esperada**: Status 200 con evaluación de beliefs

### **Paso 7: Obtener Mejor Belief**
- **Request**: `💡 Obtener Mejor Belief`
- **Método**: GET
- **URL**: `{{base_url}}/beliefs/best/{{game_id}}`
- **Propósito**: Ver cuál belief tiene mayor valor
- **Respuesta Esperada**: Belief con mayor valor y su tipo

### **Paso 8: Ejecutar Acción del Belief**
- **Request**: `🎯 Ejecutar Acción del Belief`
- **Método**: POST
- **URL**: `{{base_url}}/beliefs/action`
- **Body**:
```json
{
  "game_id": "{{game_id}}",
  "belief_type": "advice"
}
```
- **Propósito**: Ejecutar la acción del belief seleccionado
- **Respuesta Esperada**: Mensaje personalizado basado en el belief

### **Paso 9: Ver Métricas del Jugador**
- **Request**: `📈 Obtener Métricas del Jugador`
- **Método**: GET
- **URL**: `{{base_url}}/game/{{game_id}}/metrics`
- **Propósito**: Ver métricas calculadas por el sistema
- **Respuesta Esperada**: Métricas como tries_count, misses_count, buclicity, etc.

### **Paso 10: Simular Movimiento Incorrecto**
- **Request**: `🎮 Movimiento Incorrecto (Simular Error)`
- **Método**: POST
- **URL**: `{{base_url}}/game/move`
- **Body**:
```json
{
  "game_id": "{{game_id}}",
  "movement": [3, 2, 1, -1, 0, -2, -3]
}
```
- **Propósito**: Simular un error para activar beliefs de ayuda
- **Respuesta Esperada**: Status 400 o mensaje de error

### **Paso 11: Simular Movimiento Repetitivo**
- **Request**: `🔄 Movimiento Repetitivo (Simular Buclicity)`
- **Método**: POST
- **URL**: `{{base_url}}/game/move`
- **Body**:
```json
{
  "game_id": "{{game_id}}",
  "movement": [3, 2, 1, 0, -1, -2, -3]
}
```
- **Propósito**: Simular patrón repetitivo para detectar buclicity
- **Respuesta Esperada**: Status 200 con posible advertencia

### **Paso 12: Completar el Juego**
- **Request**: `🏆 Completar Juego`
- **Método**: POST
- **URL**: `{{base_url}}/game/move`
- **Body**:
```json
{
  "game_id": "{{game_id}}",
  "movement": [-3, -2, -1, 0, 1, 2, 3]
}
```
- **Propósito**: Llegar al estado objetivo del juego
- **Respuesta Esperada**: Status 200 con mensaje de victoria

### **Paso 13: Ver Beliefs Finales**
- **Request**: `📊 Beliefs Finales`
- **Método**: GET
- **URL**: `{{base_url}}/beliefs/{{game_id}}/summary`
- **Propósito**: Ver resumen final de todos los beliefs
- **Respuesta Esperada**: Resumen completo de beliefs y acciones

### **Paso 14: Debug del Estado**
- **Request**: `🔍 Debug - Estado de la Base de Datos`
- **Método**: GET
- **URL**: `{{base_url}}/debug/game/{{game_id}}`
- **Propósito**: Ver estado completo en la base de datos
- **Respuesta Esperada**: Información detallada del juego

## 🔍 **Análisis de Respuestas**

### **Respuestas del Sistema de Beliefs**

#### **AdviceController**
- **Alto valor**: Sugiere reducir dificultad o crear nuevo intento
- **Medio valor**: Proporciona consejos estratégicos
- **Bajo valor**: Mensaje de motivación

#### **FeedbackController**
- **Alto valor**: Feedback detallado con sugerencias específicas
- **Medio valor**: Feedback moderado con áreas de mejora
- **Bajo valor**: Felicitaciones por buen progreso

#### **ExplainController**
- **Alto valor**: Explicación completa de reglas
- **Medio valor**: Recordatorio de reglas básicas
- **Bajo valor**: Confirmación de comprensión

#### **DemonstrateController**
- **Alto valor**: Muestra movimiento óptimo
- **Medio valor**: Lista movimientos posibles
- **Bajo valor**: Pistas estratégicas

#### **AskController**
- **Alto valor**: Preguntas estratégicas profundas
- **Medio valor**: Preguntas de comprensión
- **Bajo valor**: Preguntas motivacionales

### **Métricas Clave a Observar**

1. **tries_count**: Número de intentos
2. **misses_count**: Errores cometidos
3. **buclicity**: Patrones repetitivos
4. **branch_factor**: Diversidad de movimientos
5. **belief_values**: Valores de cada belief (0.0-1.0)

## 🚨 **Solución de Problemas**

### **Error: "Connection refused"**
- Verifica que el servidor esté ejecutándose
- Confirma que el puerto 8000 esté disponible

### **Error: "Database connection failed"**
- Verifica que PostgreSQL esté ejecutándose
- Confirma las credenciales en el archivo `.env`

### **Error: "Module not found"**
- Instala las dependencias: `pip install -r requirements.txt`
- Verifica que estés en el directorio correcto

### **Error: "Invalid game_id"**
- Asegúrate de ejecutar las requests en orden
- Verifica que las variables se estén llenando correctamente

## 📊 **Interpretación de Resultados**

### **Belief Values (0.0 - 1.0)**
- **0.0-0.3**: Baja necesidad de intervención
- **0.3-0.6**: Necesidad moderada de ayuda
- **0.6-1.0**: Alta necesidad de intervención

### **Patrones de Comportamiento**
- **Alta buclicity**: Jugador atascado en patrones
- **Muchos errores**: Necesita explicación de reglas
- **Tiempo alto**: Posible desmotivación
- **Pocos movimientos**: Estrategia limitada

## 🔄 **Pruebas Adicionales**

### **Cambiar Dificultad**
1. Modifica la variable `difficulty` a 2 o 3
2. Ejecuta el flujo completo nuevamente
3. Observa cómo cambian los beliefs

### **Simular Diferentes Escenarios**
1. **Jugador Experto**: Movimientos rápidos y correctos
2. **Jugador Novato**: Muchos errores y tiempo alto
3. **Jugador Atascado**: Movimientos repetitivos

### **Probar Diferentes Beliefs**
1. Ejecuta `beliefs/evaluate` múltiples veces
2. Observa cómo evolucionan los valores
3. Compara respuestas de diferentes beliefs

## 📈 **Métricas de Rendimiento**

### **Tiempos de Respuesta Esperados**
- **Health Check**: < 100ms
- **Crear Juego**: < 500ms
- **Evaluar Beliefs**: < 1000ms
- **Ejecutar Acción**: < 500ms

### **Uso de Recursos**
- **CPU**: < 20% durante operaciones normales
- **Memoria**: < 100MB para el servidor
- **Base de Datos**: < 50 conexiones simultáneas

## 🎯 **Objetivos de las Pruebas**

1. **Verificar Funcionamiento**: Todos los endpoints responden correctamente
2. **Validar Beliefs**: El sistema adaptativo funciona según las métricas
3. **Probar Adaptabilidad**: Los beliefs cambian según el comportamiento
4. **Verificar Persistencia**: Los datos se guardan correctamente en la BD
5. **Validar Lógica**: Las respuestas son apropiadas para cada situación

---

**Nota**: Esta guía asume que todos los endpoints están implementados en el servidor. Si algún endpoint no existe, necesitarás implementarlo primero o modificar la colección según la funcionalidad disponible.
