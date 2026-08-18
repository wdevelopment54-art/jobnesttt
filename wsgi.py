"""WSGI entry point for PythonAnywhere deployment.

Paste the contents of this file into the WSGI configuration file shown in the
PythonAnywhere "Web" tab (e.g. /var/www/jobnesteee_pythonanywhere_com_wsgi.py).

IMPORTANT — why this file looks the way it does
------------------------------------------------
PythonAnywhere's WSGI file lives in /var/www/, so when this code runs there,
``__file__`` points at /var/www/<user>_pythonanywhere_com_wsgi.py — NOT at your
project folder. A naive ``PROJECT_ROOT = os.path.dirname(__file__)`` therefore
resolves to /var/www/, which means:

  * your project packages (``app``, ``utils``, ``models``, ``routes``...) are
    not importable  ->  ModuleNotFoundError  ->  the WSGI app never loads,
  * and you get the classic "Error code: 502-backend" page.

To avoid that, we derive the username from the WSGI filename
(``<user>_pythonanywhere_com_wsgi.py``) and then scan the user's home directory
for the folder that actually contains ``app.py``. If this file is run locally
(not on PythonAnywhere) we fall back to its own directory.
"""

import os
import re
import sys


def _find_project_root():
    """Locate the directory that contains this project's app.py.

    Works both when pasted into PythonAnywhere's /var/www/ WSGI file and when
    run directly (e.g. ``python wsgi.py`` locally).
    """
    here = os.path.abspath(__file__)
    wsgi_filename = os.path.basename(here)

    # Running on PythonAnywhere?  Filename looks like:
    #   <username>_pythonanywhere_com_wsgi.py
    match = re.match(r"^(.+)_pythonanywhere_com_wsgi\.py$", wsgi_filename)
    if match:
        username = match.group(1)
        home = f"/home/{username}"
        # Scan the home directory for any folder that contains app.py, so the
        # project works regardless of the folder name (jobnest, mysite, etc.).
        if os.path.isdir(home):
            for name in os.listdir(home):
                candidate = os.path.join(home, name)
                if os.path.isfile(os.path.join(candidate, "app.py")):
                    return candidate
        # Fall back to the home directory even if app.py wasn't found there
        # yet (so the error message is about the real missing module, not /var/www).
        return home

    # Not on PythonAnywhere: assume this file sits in the project root.
    return os.path.dirname(here)


PROJECT_ROOT = _find_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# 2. Load environment variables from the project's .env file (if present).
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    # python-dotenv is not installed; environment variables must be set
    # directly in the PythonAnywhere "Environment variables" section.
    pass


# ---------------------------------------------------------------------------
# 3. Import and create the application.
# ---------------------------------------------------------------------------
from app import create_app

application = create_app(os.environ.get("FLASK_ENV", "production"))

# PythonAnywhere expects a WSGI callable named `application`.
if __name__ == "__main__":
    application.run()
