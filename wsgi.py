"""WSGI entry point for production deployment (e.g. gunicorn wsgi:app)."""

import os
import sys

# Ensure the project root is on sys.path so top-level packages are importable.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app import create_app

config_name = os.environ.get("FLASK_ENV", "production")
app = create_app(config_name)

if __name__ == "__main__":
    app.run()
