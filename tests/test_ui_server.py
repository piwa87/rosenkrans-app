"""Tests for the Flask UI server."""

from localization import LanguageSettings
from rosary_state import RosaryStateMachine
from ui.server import create_app


def test_index_renders_language_switch():
    app = create_app(RosaryStateMachine(), LanguageSettings())

    with app.test_client() as client:
        response = client.get("/")

    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'id="language-select"' in html
    assert 'value="da"' in html


def test_language_endpoint_switches_to_danish():
    app = create_app(RosaryStateMachine(), LanguageSettings())

    with app.test_client() as client:
        response = client.post("/language", json={"language": "da"})

    assert response.status_code == 200
    assert response.get_json()["language"] == "da"


def test_language_endpoint_rejects_unknown_language():
    app = create_app(RosaryStateMachine(), LanguageSettings())

    with app.test_client() as client:
        response = client.post("/language", json={"language": "de"})

    assert response.status_code == 400
