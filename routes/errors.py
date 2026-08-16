from flask import Blueprint, render_template, request, jsonify

from utils import get_site_settings

bp = Blueprint("errors", __name__)


@bp.app_errorhandler(404)
def not_found(error):
    settings = get_site_settings()
    return render_template("errors/404.html", settings=settings, title="Page Not Found"), 404


@bp.app_errorhandler(403)
def forbidden(error):
    settings = get_site_settings()
    return render_template("errors/403.html", settings=settings, title="Forbidden"), 403


@bp.app_errorhandler(500)
def internal_error(error):
    settings = get_site_settings()
    return render_template("errors/500.html", settings=settings, title="Server Error"), 500
