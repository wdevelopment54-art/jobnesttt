"""Create or reset the admin account for JobNest.

Run on the server (PythonAnywhere Bash console) from the project root:

    python create_admin.py

It will create the admin user if it does not exist, or reset the
password/email/role of an existing admin so you can always log in.
Overrides the defaults with environment variables ADMIN_EMAIL and
ADMIN_PASSWORD (loaded from the project's .env file if present).
"""

import os
import sys

# Load .env from the project root explicitly. The Bash console CWD is usually
# the project dir, but be explicit so ADMIN_EMAIL/ADMIN_PASSWORD from .env are
# always picked up regardless of how this script is launched.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
except ImportError:
    pass

from app import create_app
from extensions import db
from models import User


def main():
    email = os.environ.get("ADMIN_EMAIL", "admin@example.com").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "Admin@123456")
    name = os.environ.get("ADMIN_NAME", "Site Administrator")

    app = create_app(os.environ.get("FLASK_ENV", "production"))
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(full_name=name, email=email, phone="", role="admin")
            db.session.add(user)
            action = "Created"
        else:
            user.role = "admin"
            user.is_active = True
            user.full_name = name
            action = "Updated"

        user.set_password(password)
        db.session.commit()
        print(f"{action} admin account: {email}")


if __name__ == "__main__":
    main()
