import sqlite3

from fastapi.testclient import TestClient

from app.main import create_app
from app.security import verify_password


def test_api(database_path):
    client = TestClient(create_app(database_path))
    assert client.get("/api/categories").json() == {"tags": ["Action", "Adventure", "Drama"]}
    assert client.get("/api/animes?q=acao").json()["pagination"]["total_items"] == 2
    assert client.get("/api/animes/A1").json()["series_metadata"]["episode_count"] == 12
    assert client.get("/api/animes/nope").status_code == 404
    assert client.get("/api/animes?page=0").status_code == 422


def test_register_user_and_reject_duplicate_username(tmp_path):
    database_path = tmp_path / "users.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )

    client = TestClient(create_app(database_path))
    response = client.post(
        "/register",
        data={"username": "  sample-user  ", "password": "secret"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert client.cookies

    with sqlite3.connect(database_path) as connection:
        username, stored_hash = connection.execute(
            "SELECT username, password_hash FROM users"
        ).fetchone()

    assert username == "sample-user"
    assert stored_hash != "secret"
    assert verify_password("secret", stored_hash)

    duplicate = client.post(
        "/register",
        data={"username": "sample-user", "password": "another-secret"},
    )
    assert duplicate.status_code == 409
    assert "Este usuário já está cadastrado." in duplicate.text


def test_login_page_includes_registration_modal():
    client = TestClient(create_app("unused.db"))

    response = client.get("/login")

    assert response.status_code == 200
    assert 'id="register-dialog"' in response.text
    assert 'action="/register"' in response.text
