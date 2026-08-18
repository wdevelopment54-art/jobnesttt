"""Application factory for the Job Portal."""

import os
import sys

# Ensure the project root is on sys.path so top-level packages like
# `utils`, `models`, `forms`, and `routes` are importable regardless of how
# the WSGI server (e.g. PythonAnywhere) sets up the path.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from flask import Flask, render_template, request, session
from flask_login import LoginManager
from dotenv import load_dotenv
from sqlalchemy import inspect, text

from config import config_by_name
from extensions import db, csrf
from utils import get_site_settings

# Load .env from the project root explicitly. On PythonAnywhere the WSGI
# process runs with CWD=/var/www/, so a bare load_dotenv() looks in the
# wrong directory and silently fails to load the project's .env (which is
# why custom ADMIN_EMAIL/ADMIN_PASSWORD from .env were not applied).
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.login_message = "Please log in to access this page."


def _migrate_schema(app):
    """Add any columns present on the models but missing from existing SQLite
    tables.

    ``db.create_all()`` only creates tables that do not yet exist; it does NOT
    add new columns to tables that were created by an earlier version of the
    models. Without this, a freshly added column (e.g. ``SiteSettings.about_banner``)
    raises ``no such column`` on every request and the whole site 500s. This
    keeps the deployed database in sync with the models without an external
    migration tool.
    """
    from models import Base
    inspector = inspect(db.engine)
    with app.app_context():
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                # Build the ADD COLUMN SQL using the column's compiled DDL.
                col_type = column.type.compile(db.engine.dialect)
                nullable = "" if column.nullable else " NOT NULL"
                # Only emit a literal DEFAULT for simple scalar values. Function
                # defaults (e.g. datetime.utcnow) cannot be expressed as a SQL
                # literal and are instead applied on the next row write, so we
                # skip them here.
                default = ""
                col_default = getattr(column, "default", None)
                if col_default is not None and getattr(col_default, "is_scalar", False):
                    arg = col_default.arg
                    if isinstance(arg, str):
                        default = f" DEFAULT '{arg}'"
                    elif isinstance(arg, bool):
                        default = f" DEFAULT {1 if arg else 0}"
                    else:
                        default = f" DEFAULT {arg}"
                sql = (f"ALTER TABLE {table.name} ADD COLUMN "
                       f"{column.name} {col_type}{nullable}{default}")
                try:
                    with db.engine.begin() as conn:
                        conn.execute(text(sql))
                except Exception as exc:  # pragma: no cover - defensive
                    app.logger.warning("Schema migration skipped for %s.%s: %s",
                                       table.name, column.name, exc)


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure instance folder exists
    os.makedirs(os.path.dirname(os.path.join(app.config["BASE_DIR"], app.config["DATABASE_PATH"])), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from routes import auth, public, seeker, employer, admin, errors
    app.register_blueprint(auth.bp)
    app.register_blueprint(public.bp)
    app.register_blueprint(seeker.bp)
    app.register_blueprint(employer.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(errors.bp)

    # Make Category available in templates (used by footer)
    from models import Category
    app.jinja_env.globals['Category'] = Category

    # Context processors
    @app.context_processor
    def inject_settings():
        settings = get_site_settings()
        return dict(settings=settings)

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        unread_notifications = 0
        if current_user.is_authenticated:
            unread_notifications = current_user.notifications.filter_by(is_read=False).count()
        return dict(unread_notifications=unread_notifications)

    # Custom filters
    @app.template_filter("format_currency")
    @app.template_filter("nl2br")
    def nl2br(value):
        if not value:
            return ""
        return value.replace("\n", "<br>")

    def format_currency(value):
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value) if value else "0"

    # Maintenance mode check
    @app.before_request
    def check_maintenance():
        from models import SiteSettings
        settings = SiteSettings.query.first()
        if settings and settings.maintenance_mode:
            # Allow admin access and static files
            if request.endpoint and (
                request.endpoint.startswith("admin.")
                or request.endpoint in ("auth.login", "auth.logout", "static")
            ):
                return
            # Allow admin login route
            if request.endpoint == "auth.login":
                return
            if request.path.startswith("/admin"):
                return
            return render_template("maintenance.html", settings=settings)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Create database + seed
    with app.app_context():
        db.create_all()
        _migrate_schema(app)
        _seed_initial_data(app)

    return app


def _seed_initial_data(app):
    """Create or update the configured admin account and seed categories.

    Unlike a one-time seed, this guarantees the admin account defined by
    ADMIN_EMAIL/ADMIN_PASSWORD in the environment (or .env) always exists
    with the correct password, even if another admin was previously created.
    """
    from models import User, SiteSettings, Category

    admin_email = app.config.get("ADMIN_EMAIL", "admin@example.com").strip().lower()
    admin_password = app.config.get("ADMIN_PASSWORD", "Admin@123456")
    admin_name = app.config.get("ADMIN_NAME", "Site Administrator")

    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(full_name=admin_name, email=admin_email, phone="", role="admin")
        db.session.add(admin)
    else:
        # Keep the configured admin valid (role + active) in case it was changed.
        admin.role = "admin"
        admin.is_active = True
        admin.full_name = admin_name
    admin.set_password(admin_password)
    db.session.flush()

    # Site settings
    if not SiteSettings.query.first():
        db.session.add(SiteSettings())

    # Categories
    if not Category.query.first():
        defaults = [
            ("Software Development", "Build and maintain software applications."),
            ("Data Science & Analytics", "Extract insights from data."),
            ("Design & Creative", "Craft beautiful user experiences."),
            ("Marketing", "Grow brands and reach audiences."),
            ("Sales", "Drive revenue and build relationships."),
            ("Customer Service", "Support and delight customers."),
            ("Finance & Accounting", "Manage money and compliance."),
            ("Human Resources", "Build and support great teams."),
            ("Healthcare", "Care for communities and patients."),
            ("Engineering", "Design and operate physical systems."),
            ("Education", "Teach and enable learning."),
            ("Operations & Logistics", "Keep the business moving."),
        ]
        for i, (name, desc) in enumerate(defaults):
            db.session.add(Category(name=name, description=desc, sort_order=i))

    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)


# Module-level app instance for WSGI servers (e.g. PythonAnywhere's
# default WSGI file does `from app import app as application`).
app = create_app(os.environ.get("FLASK_ENV", "production"))
