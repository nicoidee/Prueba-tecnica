from __future__ import annotations

import pytest
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

try:
    from litestar.testing import TestClient
except Exception:
    TestClient = None


def test_pytest_discovers_tests() -> None:
    # Smoke test: confirma que pytest esta leyendo este archivo.
    assert 1 + 1 == 2


@pytest.mark.skipif(TestClient is None, reason="Litestar TestClient no disponible")
def test_login_ok_returns_200_or_201_and_sets_cookie() -> None:
    from backend.app import app

    with TestClient(app=app) as client:
        r = client.post(
            "/auth/login",
            json={"username": "jhon_doe_1", "password": "password"},
        )
        assert r.status_code in (HTTP_200_OK, HTTP_201_CREATED)
        assert r.headers.get("set-cookie") is not None


@pytest.mark.skipif(TestClient is None, reason="Litestar TestClient no disponible")
def test_login_bad_password_returns_401_or_403() -> None:
    from backend.app import app

    with TestClient(app=app) as client:
        r = client.post(
            "/auth/login",
            json={"username": "jhon_doe_1", "password": "mala"},
        )
        assert r.status_code in (HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN)
