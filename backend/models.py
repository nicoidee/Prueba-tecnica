import sqlite3
from typing import Dict, List, Optional

from .db import DB_PATH


def get_user_by_username(username: str) -> Optional[Dict]:
    """Obtiene un usuario por username (sin exponer password_hash).

    Esta funcion es segura para reutilizar en endpoints donde no se necesita
    el hash (por ejemplo, para obtener datos del usuario logueado).

    Args:
        username (str): Username a buscar.

    Returns:
        Optional[Dict]: Datos del usuario si existe, o None si no existe.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, rol, renta_mensual, username FROM usuarios WHERE username = ?", (username,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "nombre": row[1],
        "rol": row[2],
        "renta_mensual": row[3],
        "username": row[4],
    }


def get_user_auth_by_username(username: str) -> Optional[Dict]:
    """Obtiene un usuario por username incluyendo password_hash (solo para login).

    Importante: esta funcion no debe usarse para responder al frontend.

    Args:
        username (str): Username a buscar.

    Returns:
        Optional[Dict]: Datos del usuario con password_hash si existe, o None si no existe.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, rol, renta_mensual, username, password_hash FROM usuarios WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
    finally:
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


def get_users_for_role(current_user_id: int, current_role: str) -> List[Dict]:
    """Retorna la lista de usuarios visibles segun el rol del usuario autenticado.

    Reglas:
    - admin: ve todos los usuarios.
    - supervisor: ve supervisores y usuarios, no ve admins.
    - usuario: solo ve su propio registro.

    Args:
        current_user_id (int): ID del usuario autenticado.
        current_role (str): Rol del usuario autenticado.

    Returns:
        List[Dict]: Lista de registros visibles con id, nombre, rol, renta_mensual.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        if current_role == "admin":
            cursor.execute("SELECT id, nombre, rol, renta_mensual FROM usuarios")

        elif current_role == "supervisor":
            cursor.execute(
                """
                SELECT id, nombre, rol, renta_mensual
                FROM usuarios
                WHERE rol IN ('supervisor', 'usuario')
                """
            )

        elif current_role == "usuario":
            cursor.execute(
                """
                SELECT id, nombre, rol, renta_mensual
                FROM usuarios
                WHERE id = ?
                """,
                (current_user_id,),
            )

        else:
            # deny by default: rol desconocido => sin resultados
            cursor.execute("SELECT id, nombre, rol, renta_mensual FROM usuarios WHERE 1=0")

        rows = cursor.fetchall()
    finally:
        conn.close()

    return [{"id": r[0], "nombre": r[1], "rol": r[2], "renta_mensual": r[3]} for r in rows]
