"""RELAY app factory. Bootstrap file (planv0.2 §1): written at SYNC-1, then frozen."""

import importlib
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

ROOT = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    load_dotenv()
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static"),
    )
    app.secret_key = os.environ.get("RELAY_SECRET_KEY", "relay-dev")

    # Product vocabulary is available to every template.
    from contracts import vocab

    app.jinja_env.globals["vocab"] = vocab
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    # Each blueprint registers once its owner has written it.
    for module, attr in [("app.routes", "bp"), ("app.preview", "bp")]:
        try:
            app.register_blueprint(getattr(importlib.import_module(module), attr))
        except ModuleNotFoundError as e:
            if e.name != module:
                raise

    return app
