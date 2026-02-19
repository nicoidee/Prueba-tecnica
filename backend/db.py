import json
import sqlite3
from pathlib import Path


# Base del archivo actual (backend/db.py) y raiz del repo
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Rutas del proyecto:
# - DB_PATH: base de datos SQLite en la raiz del repo
# - DATA_PATH: archivo JSON con los usuarios de prueba
DB_PATH = PROJECT_DIR / "prueba.db"
DATA_PATH = PROJECT_DIR / "data" / "usuarios.json"

# Hash bcrypt fijo para entorno de prueba: corresponde a la clave "password"
# Nota: en produccion, cada usuario deberia tener su propio hash generado al registrar.
TEST_PASSWORD_HASH = "$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi"


def create_connection() -> sqlite3.Connection:
    """Crea y retorna una conexion a la base de datos SQLite.

    Returns:
        sqlite3.Connection: Conexion activa hacia la base de datos.
    """
    return sqlite3.connect(str(DB_PATH))


def create_table(conn: sqlite3.Connection) -> None:
    """Crea la tabla `usuarios` si no existe.

    La tabla guarda informacion basica del usuario y credenciales (hash).
    Se usa `username` como unico para evitar duplicados.

    Args:
        conn (sqlite3.Connection): Conexion a la base de datos.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL,
            renta_mensual REAL NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.commit()


def init_db() -> None:
    """Inicializa la base de datos.

    Flujo:
    1) Crea la conexion.
    2) Asegura la existencia de la tabla `usuarios`.
    3) Si la tabla esta vacia, carga datos desde usuarios.json e inserta registros.
    4) Cierra la conexion.

    Notas:
    - El username se genera a partir del nombre + id para que sea deterministico.
    - Se inserta un password_hash fijo (bcrypt) para pruebas, clave: "password".
    """
    conn = create_connection()
    try:
        create_table(conn)

        # Si la tabla esta vacia, se cargan usuarios desde el JSON
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        row = cursor.fetchone()
        count = row[0] if row else 0

        if count == 0:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                users_data = json.load(f)

            for user in users_data:
                # Normaliza el nombre para construir el username
                # Ejemplo: "Juan Perez" + id 2 => "juan_perez_2"
                username = f"{user['nombre'].lower().replace(' ', '_')}_{user['id']}"

                cursor.execute(
                    """
                    INSERT INTO usuarios (id, nombre, rol, renta_mensual, username, password_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user["id"],
                        user["nombre"],
                        user["rol"],
                        user["renta_mensual"],
                        username,
                        TEST_PASSWORD_HASH,
                    ),
                )

            conn.commit()
            print(f"DB poblada con {len(users_data)} usuarios")
    finally:
        # Se asegura el cierre de la conexion aunque ocurra un error
        conn.close()
