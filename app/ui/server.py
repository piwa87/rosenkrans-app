"""Flask web server: exposes the rosary state via REST and Server-Sent Events."""

import json
import logging
import os
import queue
import threading

from flask import Flask, Response, jsonify, request, send_from_directory

from localization import LanguageSettings, SUPPORTED_LANGUAGES, normalize_language
from rosary_state import RosaryStateMachine

logger = logging.getLogger(__name__)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# ---------------------------------------------------------------------------
# Broadcast helpers — module-level so they work before create_app is called
# ---------------------------------------------------------------------------

_clients: list[queue.Queue] = []
_clients_lock = threading.Lock()


def broadcast_event(event: dict) -> None:
    """Push an SSE event to every connected browser client."""
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(event)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _clients.remove(q)


# ---------------------------------------------------------------------------
# Flask app factory
# ---------------------------------------------------------------------------

def create_app(
    state_machine: RosaryStateMachine,
    language_settings: LanguageSettings,
    detector=None,
) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder=_STATIC_DIR, static_url_path="/static")
    app.state_machine = state_machine          # type: ignore[attr-defined]
    app.language_settings = language_settings  # type: ignore[attr-defined]
    app.detector = detector                    # type: ignore[attr-defined]
    app.broadcast_event = broadcast_event      # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Static frontend
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        return send_from_directory(_STATIC_DIR, "index.html")

    # ------------------------------------------------------------------
    # State API
    # ------------------------------------------------------------------

    @app.route("/state")
    def get_state():
        return jsonify(app.state_machine.get_state().to_dict())  # type: ignore[attr-defined]

    @app.route("/advance", methods=["POST"])
    def advance_manual():
        """Manually advance the rosary by one step (Next Bead button)."""
        state = app.state_machine.advance_manual()  # type: ignore[attr-defined]
        broadcast_event({"state": state.to_dict(), "transcript": "[manual]"})
        return jsonify(state.to_dict())

    @app.route("/undo", methods=["POST"])
    def undo():
        """Undo the last state change."""
        state = app.state_machine.undo()  # type: ignore[attr-defined]
        if state is None:
            return jsonify({"error": "Nothing to undo"}), 400
        broadcast_event({"state": state.to_dict(), "transcript": "[undo]"})
        return jsonify(state.to_dict())

    @app.route("/reset", methods=["POST"])
    def reset():
        """Reset the rosary to the beginning."""
        app.state_machine.reset()  # type: ignore[attr-defined]
        state = app.state_machine.get_state()  # type: ignore[attr-defined]
        broadcast_event({"state": state.to_dict(), "transcript": "[reset]"})
        return jsonify(state.to_dict())

    @app.route("/transcript", methods=["POST"])
    def process_transcript():
        """
        Accept a transcript from the browser Web Speech API.

        Used in mobile / web-STT mode where the browser handles mic capture
        and sends the recognised text here for prayer detection.  The backend
        runs the same PrayerDetector logic as the Python audio pipeline and
        broadcasts the result to all SSE clients.
        """
        payload = request.get_json(silent=True) or {}
        transcript = (payload.get("transcript") or "").strip()
        if not transcript:
            return jsonify({"error": "empty transcript"}), 400

        lang = normalize_language(
            payload.get("language") or app.language_settings.get_language()  # type: ignore[attr-defined]
        )

        det = app.detector  # type: ignore[attr-defined]
        if det is not None:
            prayer = det.detect(transcript, language=lang)
        else:
            prayer = None

        if prayer is not None:
            state = app.state_machine.advance(prayer)  # type: ignore[attr-defined]
        else:
            state = app.state_machine.get_state()  # type: ignore[attr-defined]

        broadcast_event({"state": state.to_dict(), "transcript": transcript})
        return jsonify(state.to_dict())

    # ------------------------------------------------------------------
    # Language API
    # ------------------------------------------------------------------

    @app.route("/language", methods=["GET", "POST"])
    def language():
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            selected = payload.get("language")
            if selected not in SUPPORTED_LANGUAGES:
                return jsonify({"error": "Unsupported language"}), 400
            current = app.language_settings.set_language(selected)  # type: ignore[attr-defined]
        else:
            current = app.language_settings.get_language()  # type: ignore[attr-defined]

        return jsonify({"language": current, "supported_languages": SUPPORTED_LANGUAGES})

    # ------------------------------------------------------------------
    # Server-Sent Events
    # ------------------------------------------------------------------

    @app.route("/stream")
    def stream():
        """
        Server-Sent Events endpoint.

        Each connected client gets its own queue.  Events are pushed immediately
        when state changes (manual advance, undo, reset, or speech detection).
        A heartbeat is sent every 25 s to keep the connection alive through
        proxies and browser timeouts.
        """
        client_q: queue.Queue = queue.Queue(maxsize=50)
        with _clients_lock:
            _clients.append(client_q)

        def event_generator():
            # Send current state immediately on connect
            initial = app.state_machine.get_state().to_dict()  # type: ignore[attr-defined]
            yield f"data: {json.dumps({'state': initial, 'transcript': ''})}\n\n"

            try:
                while True:
                    try:
                        event = client_q.get(timeout=25)
                        yield f"data: {json.dumps(event)}\n\n"
                    except queue.Empty:
                        yield 'data: {"heartbeat": true}\n\n'
            finally:
                with _clients_lock:
                    if client_q in _clients:
                        _clients.remove(client_q)

        return Response(
            event_generator(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


def start_ui(app: Flask, host: str = "127.0.0.1", port: int = 5000) -> None:
    """Start the Flask development server (call from a background thread)."""
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
