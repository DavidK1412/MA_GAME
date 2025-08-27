#!/usr/bin/env python3
"""
Script para iniciar el servidor del juego de ranas con sistema de beliefs.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Verificar versión de Python."""
    if sys.version_info < (3, 8):
        print("❌ Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def check_dependencies():
    """Verificar dependencias instaladas."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'psycopg2-binary',
        'pydantic',
        'networkx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} instalado")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} no encontrado")
    
    if missing_packages:
        print(f"\n📦 Instalando dependencias faltantes...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ Dependencias instaladas correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando dependencias: {e}")
            return False
    
    return True

def check_environment():
    """Verificar archivo de entorno."""
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  Archivo .env no encontrado")
        print("   Creando archivo .env con valores por defecto...")
        
        env_content = """# Database Configuration
PGHOST=localhost
PGPORT=5432
PGDATABASE=frog_game
PGUSER=postgres
PGPASSWORD=password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/frog_game.log

# Game Configuration
MAX_TRIES=20
TIME_LIMIT=300

# Belief System Configuration
BELIEF_UPDATE_INTERVAL=5
BELIEF_THRESHOLD=0.5
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Archivo .env creado")
        print("   ⚠️  Ajusta las credenciales de la base de datos según tu configuración")
    else:
        print("✅ Archivo .env encontrado")
    
    return True

def check_database():
    """Verificar conexión a la base de datos."""
    try:
        from app.utils.database import DatabaseClient
        
        db_client = DatabaseClient()
        db_client.connect()
        
        # Probar conexión
        result = db_client.fetch_results("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            print("✅ Conexión a base de datos exitosa")
            db_client.close()
            return True
        else:
            print("❌ Error en consulta de prueba")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        print("   Verifica que PostgreSQL esté ejecutándose")
        print("   Confirma las credenciales en el archivo .env")
        return False

def run_migrations():
    """Ejecutar migraciones de la base de datos."""
    print("\n🗄️  Ejecutando migraciones de la base de datos...")
    
    try:
        # Crear directorio de logs si no existe
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Ejecutar migración inicial
        from app.utils.database import DatabaseClient
        db_client = DatabaseClient()
        db_client.connect()
        
        # Leer archivo de migración
        migration_file = Path('db/migrations/001_initial_schema.sql')
        if migration_file.exists():
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            # Ejecutar migración
            db_client.execute_query(migration_sql)
            print("✅ Migración inicial ejecutada")
        else:
            print("⚠️  Archivo de migración inicial no encontrado")
        
        # Ejecutar migración de beliefs
        beliefs_migration = Path('db/migrations/002_add_belief_fields.sql')
        if beliefs_migration.exists():
            with open(beliefs_migration, 'r', encoding='utf-8') as f:
                beliefs_sql = f.read()
            
            # Ejecutar migración
            db_client.execute_query(beliefs_sql)
            print("✅ Migración de beliefs ejecutada")
        else:
            print("⚠️  Archivo de migración de beliefs no encontrado")
        
        db_client.close()
        
    except Exception as e:
        print(f"❌ Error ejecutando migraciones: {e}")
        return False
    
    return True

def start_server():
    """Iniciar el servidor FastAPI."""
    print("\n🚀 Iniciando servidor...")
    
    try:
        # Verificar que el archivo main.py existe
        main_file = Path('app/main.py')
        if not main_file.exists():
            print("❌ Archivo app/main.py no encontrado")
            return False
        
        # Iniciar servidor con uvicorn
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'app.main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ]
        
        print(f"   Comando: {' '.join(cmd)}")
        print("   Servidor iniciando en http://localhost:8000")
        print("   Presiona Ctrl+C para detener")
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return False
    
    return True

def main():
    """Función principal."""
    print("🐸 Iniciando Juego de Ranas con Sistema de Beliefs")
    print("=" * 50)
    
    # Verificaciones previas
    if not check_python_version():
        return 1
    
    if not check_dependencies():
        return 1
    
    if not check_environment():
        return 1
    
    if not check_database():
        return 1
    
    if not run_migrations():
        return 1
    
    # Iniciar servidor
    if not start_server():
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
