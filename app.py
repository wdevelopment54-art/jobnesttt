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

from config import config_by_name
from extensions import db, csrf
from utils import get_site_settings

load_dotenv()

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
login_manager.login_message = "Please log in to access this page."


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
        _seed_initial_data(app)

    return app


def _seed_initial_data(app):
    """Create admin account and seed categories if they do not exist."""
    from models import User, SiteSettings, Category
    from utils import slugify

    # Admin
    if not User.query.filter_by(role="admin").first():
        admin = User(
            full_name=app.config.get("ADMIN_NAME", "Site Administrator"),
            email=app.config.get("ADMIN_EMAIL", "admin@example.com"),
            phone="",
            role="admin",
        )
        admin.set_password(app.config.get("ADMIN_PASSWORD", "Admin@123456"))
        db.session.add(admin)

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
