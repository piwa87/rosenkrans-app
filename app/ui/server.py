"""Flask web server: exposes the rosary state via REST and Server-Sent Events."""

import json
import logging
import os
import time

from flask import Flask, Response, jsonify, request, send_from_directory

from localization import LanguageSettings, SUPPORTED_LANGUAGES
from rosary_state import RosaryStateMachine

logger = logging.getLogger(__name__)

# Path to the Angular production build output (relative to this file)
_ANGULAR_DIST = os.path.join(
    os.path.dirname(__file__), "frontend", "dist", "frontend", "browser"
)


def create_app(
    state_machine: RosaryStateMachine,
    language_settings: LanguageSettings,
) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder=_ANGULAR_DIST,
        static_url_path="/",
    )
    # Attach the shared state machine to the app object so all views can use it
    app.state_machine = state_machine  # type: ignore[attr-defined]
    app.language_settings = language_settings  # type: ignore[attr-defined]

    @app.route("/")
    def index():
        """Serve the Angular SPA entry point."""
        return send_from_directory(_ANGULAR_DIST, "index.html")

    @app.route("/state")
    def get_state():
        """Return the current rosary state as JSON (used for initial page load)."""
        return jsonify(app.state_machine.get_state().to_dict())  # type: ignore[attr-defined]

    @app.route("/language", methods=["GET", "POST"])
    def language():
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            selected_language = payload.get("language")
            if selected_language not in SUPPORTED_LANGUAGES:
                return jsonify({"error": "Unsupported language"}), 400
            current_language = app.language_settings.set_language(selected_language)  # type: ignore[attr-defined]
        else:
            current_language = app.language_settings.get_language()  # type: ignore[attr-defined]

        return jsonify(
            {
                "language": current_language,
                "supported_languages": SUPPORTED_LANGUAGES,
            }
        )

    @app.route("/stream")
    def stream():
        """
        Server-Sent Events endpoint.
        The browser receives a state update whenever the state changes, and at
        most every 500 ms so the page stays alive even without changes.
        """

        def event_generator():
            last_state: dict | None = None
            while True:
                current = app.state_machine.get_state().to_dict()  # type: ignore[attr-defined]
                if current != last_state:
                    last_state = current
                    yield f"data: {json.dumps(current)}\n\n"
                time.sleep(0.5)

        return Response(
            event_generator(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return app


def start_ui(app: Flask, host: str = "127.0.0.1", port: int = 5000) -> None:
    """Start the Flask development server (call from a background thread)."""
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
