"""Tests for the Flask UI server."""

from localization import LanguageSettings
from rosary_state import DecadeState, PrayerType, RosaryStateMachine
from ui.server import create_app


def _client():
    return create_app(RosaryStateMachine(), LanguageSettings()).test_client()


# ── Index ─────────────────────────────────────────────────────────────────────

def test_index_serves_html():
    with _client() as client:
        response = client.get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in html.lower() or "<html" in html.lower()
    # Static frontend: contains the rosary SVG and control buttons
    assert "rosary-svg" in html
    assert "btn-advance" in html


# ── Language ──────────────────────────────────────────────────────────────────

def test_language_endpoint_switches_to_danish():
    with _client() as client:
        response = client.post("/language", json={"language": "da"})
    assert response.status_code == 200
    assert response.get_json()["language"] == "da"


def test_language_endpoint_rejects_unknown_language():
    with _client() as client:
        response = client.post("/language", json={"language": "de"})
    assert response.status_code == 400


# ── State ─────────────────────────────────────────────────────────────────────

def test_state_endpoint_returns_idle():
    with _client() as client:
        response = client.get("/state")
    data = response.get_json()
    assert response.status_code == 200
    assert data["state"] == "IDLE"
    assert data["decade"] == 0
    assert data["bead"] == 0


# ── Manual advance ────────────────────────────────────────────────────────────

def test_advance_endpoint_starts_first_decade():
    with _client() as client:
        response = client.post("/advance")
    data = response.get_json()
    assert response.status_code == 200
    assert data["state"] == "OUR_FATHER"
    assert data["decade"] == 1


def test_advance_endpoint_increments_bead():
    with _client() as client:
        client.post("/advance")  # → OUR_FATHER
        response = client.post("/advance")  # → HAIL_MARY bead 1
    data = response.get_json()
    assert data["state"] == "HAIL_MARY"
    assert data["bead"] == 1


# ── Undo ──────────────────────────────────────────────────────────────────────

def test_undo_endpoint_reverts_advance():
    with _client() as client:
        client.post("/advance")        # → OUR_FATHER
        response = client.post("/undo")
    data = response.get_json()
    assert response.status_code == 200
    assert data["state"] == "IDLE"


def test_undo_endpoint_returns_400_on_empty_history():
    with _client() as client:
        response = client.post("/undo")
    assert response.status_code == 400
    assert "error" in response.get_json()


# ── Reset ─────────────────────────────────────────────────────────────────────

def test_reset_endpoint_returns_idle():
    with _client() as client:
        client.post("/advance")
        client.post("/advance")
        response = client.post("/reset")
    data = response.get_json()
    assert response.status_code == 200
    assert data["state"] == "IDLE"
    assert data["decade"] == 0
