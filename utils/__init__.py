"""Utility helpers: file uploads, decorators, misc helpers."""

import os
import secrets
import string
from functools import wraps

from flask import abort, redirect, url_for, current_app, request
from flask_login import current_user

from extensions import db
from models import User, Notification, AuditLog


def slugify(text):
    """Convert text to a URL-safe slug."""
    import re
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+\s", " ", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text or "item"


# ---------------------------------------------------------------------------
# File upload helpers
# ---------------------------------------------------------------------------

def allowed_file(filename, allowed_set):
    if not filename:
        return False
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


def secure_unique_filename(filename):
    """Generate a safe, unique filename preserving the extension."""
    if not filename:
        return None
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    rand = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
    return f"{rand}.{ext}" if ext else rand


def save_upload(file_storage, subfolder, allowed_extensions):
    """Save an uploaded file to static/uploads/<subfolder> with a safe name.

    Returns the relative path (e.g. uploads/resumes/abc.pdf) or None on failure.
    """
    if not file_storage or not hasattr(file_storage, "filename") or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename, allowed_extensions):
        return None
    filename = secure_unique_filename(file_storage.filename)
    folder = os.path.join(current_app.config["BASE_DIR"], "static", "uploads", subfolder)
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, filename)
    file_storage.save(dest)
    return f"uploads/{subfolder}/{filename}"


def delete_upload(relative_path):
    if not relative_path:
        return
    path = os.path.join(current_app.config["BASE_DIR"], "static", relative_path)
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Access-control decorators
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.endpoint))
        return view(*args, **kwargs)
    return wrapped


def seeker_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_seeker:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def employer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_employer:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Notification & audit helpers
# ---------------------------------------------------------------------------

def create_notification(user_id, title, message, link=None, ntype=None):
    n = Notification(user_id=user_id, title=title, message=message, link=link, type=ntype)
    db.session.add(n)
    db.session.commit()
    return n


def log_audit(admin_id, action, target_type=None, target_id=None, description=None):
    log = AuditLog(admin_id=admin_id, action=action, target_type=target_type,
                   target_id=target_id, description=description)
    db.session.add(log)
    db.session.commit()
    return log


def get_site_settings():
    from models import SiteSettings
    settings = SiteSettings.query.first()
    if not settings:
        settings = SiteSettings()
        db.session.add(settings)
        db.session.commit()
    return settings
