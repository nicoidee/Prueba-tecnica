import bcrypt
import models
from typing import Any


def hash_password(password: str) -> bytes:
    """Genera un hash bcrypt para una clave en texto plano."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(password: str, hashed: str) -> bool:
    """Valida password (texto plano) contra un hash bcrypt almacenado (string)."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """Autentica credenciales y retorna usuario sin password_hash si son validas."""
    user = models.get_user_auth_by_username(username)

    if not user:
        return None

    if verify_password(password, user["password_hash"]):
        user.pop("password_hash", None)
        return user

    return None
