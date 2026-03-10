"""Flask web server: exposes the rosary state via REST and Server-Sent Events."""

import json
import logging
import time

from flask import Flask, Response, jsonify, render_template

from rosary_state import RosaryStateMachine

logger = logging.getLogger(__name__)


def create_app(state_machine: RosaryStateMachine) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    # Attach the shared state machine to the app object so all views can use it
    app.state_machine = state_machine  # type: ignore[attr-defined]

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/state")
    def get_state():
        """Return the current rosary state as JSON (used for initial page load)."""
        return jsonify(app.state_machine.get_state().to_dict())  # type: ignore[attr-defined]

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
