import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

class DatabaseClient:
    def __init__(self, dbname, user, password, host='localhost', port='5432'):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.connection.cursor(cursor_factory=DictCursor)
        except psycopg2.DatabaseError as e:
            print(f"Error al conectar a la base de datos: {e}")

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except psycopg2.DatabaseError as e:
            self.connection.rollback()
            print(f"Error al ejecutar la consulta: {e}")

    def fetch_results(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            results = [dict(row) for row in self.cursor.fetchall()]
            return results
        except psycopg2.DatabaseError as e:
            print(f"Error al obtener los resultados: {e}")
            return None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            print("Conexión cerrada")
