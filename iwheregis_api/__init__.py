"""
 iwhereGIS Grid Engine API - Flask application factory
"""

import logging
import os
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS


def _load_env_file(project_root: Path) -> None:
    try:
        from dotenv import load_dotenv
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except Exception:
        # Optional dependency; ignore if missing
        pass


def create_app(config_name: Optional[str] = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    _load_env_file(project_root)

    from .config import get_config

    static_folder = str(project_root / "static")
    app = Flask(__name__, static_folder=static_folder, static_url_path="")

    selected_config = get_config(config_name or os.getenv("FLASK_ENV", "development"))
    app.config.from_object(selected_config)

    app.config.setdefault("PROJECT_ROOT", str(project_root))
    app.config.setdefault("DATA_DIR", os.getenv("IWHEREGIS_DATA_DIR", str(project_root / "data")))

    CORS(app)

    log_level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(level=log_level)

    from airspace_grid.grid_manager import AirspaceGridManager
    app.config["GRID_MANAGER"] = AirspaceGridManager()

    from .routes import bp as api_bp
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def handle_not_found(error):  # type: ignore[unused-argument]
        return jsonify({"success": False, "error": "Not found"}), 404

    @app.errorhandler(400)
    def handle_bad_request(error):  # type: ignore[unused-argument]
        return jsonify({"success": False, "error": "Bad request"}), 400

    @app.errorhandler(500)
    def handle_internal_error(error):  # type: ignore[unused-argument]
        return jsonify({"success": False, "error": "服务器内部错误"}), 500

    return app