import atexit
import os

from flask import Flask, jsonify

from backend.api import api
from backend.database import init_db
from backend.services.scheduler_service import start_scheduler, stop_scheduler


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)
    app.config.update(
        HOST=os.getenv("FLASK_HOST", "127.0.0.1"),
        PORT=int(os.getenv("FLASK_PORT", "5000")),
        TESTING=testing,
    )
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.after_request
    def add_cors_headers(response):
        origin = os.getenv("CORS_ORIGIN", "http://localhost:5173")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    init_db()
    if not testing and os.getenv("DISABLE_SCHEDULER", "0") != "1":
        start_scheduler()
        atexit.register(stop_scheduler)

    return app
