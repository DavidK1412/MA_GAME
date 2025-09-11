#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de need_correct
"""

import requests
import json

# Configuración del servidor
BASE_URL = "http://localhost:8000"
GAME_ID = "test-game-123"

def test_need_correct_functionality():
    """Prueba la funcionalidad cuando need_correct es True"""
    
    print("🧪 Iniciando pruebas de funcionalidad need_correct...")
    
    # 1. Crear un nuevo juego
    print("\n1. Creando nuevo juego...")
    create_response = requests.post(f"{BASE_URL}/game", json={"game_id": GAME_ID})
    print(f"   Status: {create_response.status_code}")
    print(f"   Response: {create_response.json()}")
    
    # 2. Probar movimiento con need_correct = True
    print("\n2. Enviando movimiento con need_correct=True...")
    movement_data = {
        "movement": [1, 2, 3, 0, 4, 5, 6],
        "need_correct": True
    }
    
    move_response = requests.post(f"{BASE_URL}/game/{GAME_ID}", json=movement_data)
    print(f"   Status: {move_response.status_code}")
    print(f"   Response: {move_response.json()}")
    
    # Verificar que la respuesta indica que solo se guardó el movimiento
    if move_response.status_code == 200:
        response_data = move_response.json()
        if response_data.get("actions", {}).get("saved") == True:
            print("   ✅ Movimiento guardado correctamente sin ejecutar agentes")
        else:
            print("   ❌ Error: No se detectó que el movimiento fue solo guardado")
    else:
        print("   ❌ Error en la respuesta del servidor")
    
    # 3. Probar movimiento con need_correct = False (comportamiento normal)
    print("\n3. Enviando movimiento con need_correct=False...")
    movement_data_normal = {
        "movement": [1, 2, 0, 3, 4, 5, 6],
        "need_correct": False
    }
    
    move_response_normal = requests.post(f"{BASE_URL}/game/{GAME_ID}", json=movement_data_normal)
    print(f"   Status: {move_response_normal.status_code}")
    print(f"   Response: {move_response_normal.json()}")
    
    # Verificar que la respuesta normal incluye lógica de agentes
    if move_response_normal.status_code == 200:
        response_data = move_response_normal.json()
        if "actions" in response_data and "saved" not in response_data["actions"]:
            print("   ✅ Movimiento procesado con lógica normal de agentes")
        else:
            print("   ❌ Error: No se ejecutó la lógica normal de agentes")
    else:
        print("   ❌ Error en la respuesta del servidor")
    
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    try:
        test_need_correct_functionality()
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al servidor. Asegúrate de que esté ejecutándose en localhost:8000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
