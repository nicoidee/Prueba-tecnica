from __future__ import annotations

import json
import os
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

import bcrypt
from litestar import Litestar, get, post
from litestar.connection import Request
from litestar.exceptions import HTTPException
from litestar.response import Response
from litestar.static_files import create_static_files_router

# Rutas relativas al directorio backend/
DB_PATH = Path("../prueba.db")
DATA_PATH = Path("../data/usuarios.json")


def _slugify(text: str) -> str:
    """Normaliza un nombre para generar un username base.

    Ejemplo:
        "Valentina Rios" -> "valentina_rios"

    Reglas:
    - Quita diacriticos (tildes)
    - Pasa a minusculas
    - Reemplaza espacios por "_"
    - Mantiene solo [a-z0-9_]
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = "_".join(text.split())
    text = "".join(ch for ch in text if ch.isalnum() or ch == "_")
    return text


def init_db() -> None:
    """Crea la tabla y carga usuarios desde data/usuarios.json si esta vacia.

    Se ejecuta en on_startup para asegurar que la app tenga datos disponibles.

    Para re-seedear (si cambias el JSON o quieres regenerar credenciales), ejecuta:
        RESET_DB=1 python app.py
    """
    reset_db = os.getenv("RESET_DB") == "1"

    conn = sqlite3.connect(DB_PATH)
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

    if reset_db:
        cursor.execute("DELETE FROM usuarios")
        conn.commit()

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    count = cursor.fetchone()[0]

    # Seed solo si no hay datos
    if count == 0:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            users_data = json.load(f)

        for user in users_data:
            base = _slugify(user["nombre"])
            username = f"{base}_{user['id']}"

            # Clave por defecto para todos: "password" (hasheada con bcrypt)
            # Nota: bcrypt.gensalt() genera un salt aleatorio por usuario.
            password_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode("utf-8")

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
                    password_hash,
                ),
            )

        conn.commit()
        print(f"DB poblada con {len(users_data)} usuarios")

    conn.close()


def _get_user_by_username(username: str) -> dict[str, Any] | None:
    """Obtiene un usuario por username, incluyendo password_hash (uso interno).

    Importante:
    - Esta funcion es interna al backend.
    - Nunca se debe retornar password_hash al frontend.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, rol, renta_mensual, username, password_hash FROM usuarios WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "nombre": row[1],
        "rol": row[2],
        "renta_mensual": row[3],
        "username": row[4],
        "password_hash": row[5],
    }


def _authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """Valida credenciales contra bcrypt y retorna el usuario (sin hash) si autentica."""
    user = _get_user_by_username(username)
    if not user:
        return None

    ok = bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8"))
    if ok:
        user.pop("password_hash", None)
        return user

    return None


def _get_users_for_role(current_user_id: int, current_role: str) -> list[dict[str, Any]]:
    """Aplica reglas de visibilidad por rol y retorna la lista visible.

    Reglas:
    - admin: ve todos
    - supervisor: ve supervisor y usuario (no admin)
    - usuario: solo se ve a si mismo
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if current_role == "admin":
        cursor.execute("SELECT id, nombre, rol, renta_mensual FROM usuarios")

    elif current_role == "supervisor":
        cursor.execute(
            "SELECT id, nombre, rol, renta_mensual FROM usuarios WHERE rol IN ('supervisor', 'usuario')"
        )

    elif current_role == "usuario":
        cursor.execute(
            "SELECT id, nombre, rol, renta_mensual FROM usuarios WHERE id = ?",
            (current_user_id,),
        )

    else:
        # deny by default: rol desconocido => sin resultados
        cursor.execute("SELECT id, nombre, rol, renta_mensual FROM usuarios WHERE 1=0")

    rows = cursor.fetchall()
    conn.close()

    return [{"id": r[0], "nombre": r[1], "rol": r[2], "renta_mensual": r[3]} for r in rows]


@post("/auth/login")
async def login(request: Request) -> Response:
    """Endpoint de login.

    Recibe JSON:
        {"username": "...", "password": "..."}

    Si autentica, setea cookies HTTPOnly:
    - user_id: id del usuario autenticado
    - role: rol del usuario autenticado
    """
    data = await request.json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = _authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    response = Response(content={"message": "Login OK", "user": user})

    # Cookies para mantener sesion durante la navegacion
    # Nota: en produccion conviene setear secure=True y considerar expiracion.
    response.set_cookie("user_id", str(user["id"]), httponly=True, samesite="lax")
    response.set_cookie("role", user["rol"], httponly=True, samesite="lax")
    return response


@post("/auth/logout")
async def logout(request: Request) -> Response:
    """Endpoint de logout: elimina cookies de sesion."""
    response = Response(content={"message": "Logout OK"})
    response.delete_cookie("user_id")
    response.delete_cookie("role")
    return response


@get("/usuarios")
async def usuarios(request: Request) -> list[dict[str, Any]]:
    """Retorna la lista de usuarios visibles segun el rol guardado en cookies."""
    user_id_cookie = request.cookies.get("user_id")
    role_cookie = request.cookies.get("role")

    if not user_id_cookie or not role_cookie:
        raise HTTPException(status_code=401, detail="No autenticado")

    return _get_users_for_role(int(user_id_cookie), role_cookie)


# Router para servir el frontend (HTML/CSS/JS)
static_router = create_static_files_router(
    path="/",
    directories=["../frontend"],
    html_mode=True,
)

# API primero, estaticos al final
app = Litestar(route_handlers=[login, logout, usuarios, static_router], on_startup=[init_db])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
