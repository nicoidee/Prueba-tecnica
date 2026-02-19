from __future__ import annotations

import re
import unicodedata

import pytest
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED

try:
    from litestar.testing import TestClient
except Exception:
    TestClient = None


def _slugify_nombre(nombre: str) -> str:
    # Similar a lo tipico: quita tildes, lower, espacios a underscore, limpia simbolos.
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


@pytest.mark.skipif(TestClient is None, reason="Litestar TestClient no disponible")
def test_user_sees_only_self_or_subset() -> None:
    from backend.app import app

    # 1) Login admin
    with TestClient(app=app) as client:
        r = client.post("/auth/login", json={"username": "jhon_doe_1", "password": "password"})
        assert r.status_code in (HTTP_200_OK, HTTP_201_CREATED)

        # 2) Tomar un usuario real con rol "usuario" desde /usuarios
        r2 = client.get("/usuarios")
        assert r2.status_code == HTTP_200_OK
        all_users = r2.json()
        assert isinstance(all_users, list)
        assert len(all_users) >= 1

        candidato_id = None
        candidato_nombre = None

        for u in all_users:
            if not isinstance(u, dict):
                continue
            if str(u.get("rol", "")).lower() == "usuario":
                candidato_id = u.get("id")
                candidato_nombre = u.get("nombre")
                break

        assert candidato_id is not None, "No encontre ningun usuario con rol=usuario en /usuarios"
        assert candidato_nombre is not None, "El usuario candidato no trae 'nombre'"

        candidato_username = f"{_slugify_nombre(str(candidato_nombre))}_{int(candidato_id)}"

    # 3) Nuevo cliente: login como usuario y validar que vea solo lo suyo
    with TestClient(app=app) as client2:
        r3 = client2.post("/auth/login", json={"username": candidato_username, "password": "password"})
        assert r3.status_code in (HTTP_200_OK, HTTP_201_CREATED)

        r4 = client2.get("/usuarios")
        assert r4.status_code == HTTP_200_OK
        visibles = r4.json()
        assert isinstance(visibles, list)
        assert len(visibles) >= 1

        # Regla esperada: usuario basico ve solo su propio registro
        for item in visibles:
            assert isinstance(item, dict)
            assert int(item.get("id")) == int(candidato_id)
