"""Simple CLI to run the API server in development mode."""

import os

from . import create_app


def main() -> None:
    app = create_app(os.getenv("FLASK_ENV"))
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=app.config.get("DEBUG", True))