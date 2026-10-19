from fastapi.testclient import TestClient

from app.main import app


def test_home_is_portuguese_and_can_load_without_database_or_provider():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<html lang="pt-BR">' in response.text
    assert "Demo de portfólio" in response.text
    assert "serão enviados à NVIDIA" in response.text
    assert 'id="history"' in response.text
    assert 'id="question"' in response.text
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_frontend_assets_are_served_and_no_secret_is_exposed():
    with TestClient(app) as client:
        for path in ("style.css", "app.js", "icon.svg"):
            response = client.get(f"/static/{path}")
            assert response.status_code == 200
            assert "NVIDIA_API_KEY" not in response.text
        assert client.get("/static/does-not-exist.js").status_code == 404


def test_home_does_not_change_api_schema():
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
    assert "/" not in paths
    assert "/v1/auth/login" in paths
