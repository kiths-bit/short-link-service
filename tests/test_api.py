import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from app import app
from database import get_connection

@pytest.fixture
def client():
    app.config["TESTING"] = True

    connection = get_connection()
    connection.execute("DELETE FROM links")
    connection.commit()
    connection.close()

    with app.test_client() as client:
        yield client

    connection = get_connection()
    connection.execute("DELETE FROM links")
    connection.commit()
    connection.close()


def test_create_link(client):
    response = client.post(
        "/links",
        json={"url": "https://example.com"}
    )

    assert response.status_code == 201

    data = response.get_json()

    assert "code" in data
    assert data["url"] == "https://example.com"


def test_invalid_url_returns_400(client):
    response = client.post(
        "/links",
        json={"url": "not-a-url"}
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "url" in data["error"]


def test_missing_url_returns_400(client):
    response = client.post(
        "/links",
        json={}
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "url" in data["error"]


def test_unknown_code_returns_404(client):
    response = client.get("/links/doesnotexist")

    assert response.status_code == 404


def test_duplicate_url_returns_same_code(client):
    first = client.post(
        "/links",
        json={"url": "https://example.org"}
    )

    second = client.post(
        "/links",
        json={"url": "https://example.org"}
    )

    assert first.status_code == 201
    assert second.status_code == 200

    first_code = first.get_json()["code"]
    second_code = second.get_json()["code"]

    assert first_code == second_code


def test_redirect_and_count(client):
    create_response = client.post(
        "/links",
        json={"url": "https://example.com/page"}
    )

    code = create_response.get_json()["code"]

    redirect_response = client.get(
        f"/links/{code}",
        follow_redirects=False
    )

    assert redirect_response.status_code == 302
    assert redirect_response.headers["Location"] == "https://example.com/page"

    stats_response = client.get(f"/links/{code}/stats")

    assert stats_response.status_code == 200

    stats = stats_response.get_json()

    assert stats["clicks"] == 1


def test_malformed_input_does_not_create_link(client):
    response = client.post(
        "/links",
        json={"url": "definitely-not-valid"}
    )

    assert response.status_code == 400

    stats_response = client.get("/links/nonexistent")

    assert stats_response.status_code == 404