from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user, login_user

from extensions import db
from models import (User, UserProfile, Company, Category, Job, Application, Banner,
                    SiteSettings, ContactMessage, Notification, AuditLog, Resume,
                    Education, Experience, Skill)
from forms.admin import (CategoryForm, BannerForm, SiteSettingsForm, HomepageForm,
                         AboutForm, LegalForm, UserEditForm)
from forms.job import JobForm, ApplicationStatusForm
from forms.company import CompanyForm
from forms.auth import LoginForm
from utils import (admin_required, save_upload, delete_upload, create_notification,
                   get_site_settings, log_audit)
from config import Config

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/login", methods=["GET", "POST"])
def login():
    """Public, dedicated Admin login. Reuses the existing User auth system.
    Security is enforced here: only role=='admin' may enter the panel."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        # Logged in but not an admin -> send them to their own area safely
        flash("You do not have admin access.", "warning")
        return redirect(url_for("public.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account has been deactivated. Please contact support.", "danger")
                return render_template("auth/admin_login.html", form=form, title="Admin Login")
            if user.role != "admin":
                flash("Access denied. This portal is for administrators only.", "danger")
                return render_template("auth/admin_login.html", form=form, title="Admin Login")
            login_user(user, remember=form.remember.data)
            flash("Welcome back, Administrator.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("auth/admin_login.html", form=form, title="Admin Login")


@bp.route("/logout")
@login_required
def logout():
    from flask_login import logout_user
    logout_user()
    flash("You have been logged out of the admin panel.", "info")
    return redirect(url_for("admin.login"))


@bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    settings = get_site_settings()
    stats = {
        "users": User.query.count(),
        "seekers": User.query.filter_by(role="seeker").count(),
        "employers": User.query.filter_by(role="employer").count(),
        "companies": Company.query.count(),
        "jobs": Job.query.count(),
        "active_jobs": Job.query.filter_by(status="published").count(),
        "pending_jobs": Job.query.filter_by(status="pending").count(),
        "applications": Application.query.count(),
        "pending_apps": Application.query.filter_by(status="pending").count(),
        "messages": ContactMessage.query.count(),
        "unread_messages": ContactMessage.query.filter_by(is_read=False).count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", settings=settings, stats=stats,
                           recent_users=recent_users, recent_jobs=recent_jobs,
                           recent_messages=recent_messages, title="Admin Dashboard")


# ---------------- Users ----------------
@bp.route("/users")
@login_required
@admin_required
def users():
    settings = get_site_settings()
    page = request.args.get("page", 1, type=int)
    role = request.args.get("role", "").strip()
    keyword = request.args.get("keyword", "").strip()
    query = User.query
    if role:
        query = query.filter_by(role=role)
    if keyword:
        query = query.filter(db.or_(User.full_name.ilike(f"%{keyword}%"),
                                     User.email.ilike(f"%{keyword}%")))
    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=Config.ADMIN_PER_PAGE, error_out=False)
    return render_template("admin/users.html", users=pagination.items, pagination=pagination,
                           settings=settings, title="Users")


@bp.route("/user/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    settings = get_site_settings()
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        if user.role == "admin" and form.role.data != "admin":
            # Prevent removing the last admin
            admin_count = User.query.filter_by(role="admin").count()
            if admin_count <= 1:
                flash("Cannot change role of the only administrator.", "danger")
                return redirect(url_for("admin.edit_user", user_id=user.id))
        user.full_name = form.full_name.data.strip()
        user.email = form.email.data.strip().lower()
        user.phone = form.phone.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        db.session.commit()
        log_audit(current_user.id, "user_edit", "user", user.id, f"Edited {user.email}")
        flash("User updated.", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/edit_user.html", form=form, user=user, settings=settings,
                           title="Edit User")


@bp.route("/user/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.users"))
    if user.role == "admin":
        admin_count = User.query.filter_by(role="admin").count()
        if admin_count <= 1:
            flash("Cannot delete the only administrator.", "danger")
            return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    log_audit(current_user.id, "user_delete", "user", user_id, f"Deleted user {user.email}")
    flash("User deleted.", "info")
    return redirect(url_for("admin.users"))


@bp.route("/user/toggle/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.users"))
    user.is_active = not user.is_active
    db.session.commit()
    log_audit(current_user.id, "user_toggle", "user", user.id,
              f"Set active={user.is_active} for {user.email}")
    flash("User status updated.", "info")
    return redirect(url_for("admin.users"))


# ---------------- Companies ----------------
@bp.route("/companies")
@login_required
@admin_required
def companies():
    settings = get_site_settings()
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip()
    query = Company.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Company.created_at.desc())
    pagination = query.paginate(page=page, per_page=Config.ADMIN_PER_PAGE, error_out=False)
    return render_template("admin/companies.html", companies=pagination.items,
                           pagination=pagination, settings=settings, title="Companies")


@bp.route("/company/<int:company_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_company(company_id):
    settings = get_site_settings()
    company = Company.query.get_or_404(company_id)
    form = CompanyForm(obj=company)
    if form.validate_on_submit():
        form.populate_obj(company)
        if form.logo.data:
            delete_upload(company.logo)
            company.logo = save_upload(form.logo.data, "logos", Config.ALLOWED_IMAGE_EXTENSIONS)
        db.session.commit()
        log_audit(current_user.id, "company_edit", "company", company.id, f"Edited {company.name}")
        flash("Company updated.", "success")
        return redirect(url_for("admin.companies"))
    return render_template("admin/edit_company.html", form=form, company=company,
                           settings=settings, title="Edit Company")


@bp.route("/company/status/<int:company_id>/<status>", methods=["POST"])
@login_required
@admin_required
def company_status(company_id, status):
    company = Company.query.get_or_404(company_id)
    company.status = status
    db.session.commit()
    log_audit(current_user.id, "company_status", "company", company.id,
              f"Status -> {status}")
    flash(f"Company {status}.", "info")
    return redirect(url_for("admin.companies"))


@bp.route("/company/feature/<int:company_id>", methods=["POST"])
@login_required
@admin_required
def company_feature(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_featured = not company.is_featured
    db.session.commit()
    flash("Company featured status updated.", "info")
    return redirect(url_for("admin.companies"))


@bp.route("/company/delete/<int:company_id>", methods=["POST"])
@login_required
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    delete_upload(company.logo)
    db.session.delete(company)
    db.session.commit()
    log_audit(current_user.id, "company_delete", "company", company_id, f"Deleted {company.name}")
    flash("Company deleted.", "info")
    return redirect(url_for("admin.companies"))


# ---------------- Jobs ----------------
@bp.route("/jobs")
@login_required
@admin_required
def jobs():
    settings = get_site_settings()
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip()
    keyword = request.args.get("keyword", "").strip()
    query = Job.query
    if status:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(db.or_(Job.title.ilike(f"%{keyword}%"),
                                     Job.location.ilike(f"%{keyword}%")))
    query = query.order_by(Job.created_at.desc())
    pagination = query.paginate(page=page, per_page=Config.ADMIN_PER_PAGE, error_out=False)
    return render_template("admin/jobs.html", jobs=pagination.items, pagination=pagination,
                           settings=settings, title="Jobs")


@bp.route("/job/<int:job_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_job(job_id):
    settings = get_site_settings()
    job = Job.query.get_or_404(job_id)
    form = JobForm(obj=job)
    form.category_id.choices = [(0, "Select Category")] + [
        (c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    form.company_id.choices = [(job.company_id, job.company.name)]
    if request.method == "GET":
        form.category_id.data = job.category_id or 0
    if form.validate_on_submit():
        form.populate_obj(job)
        job.category_id = form.category_id.data or None
        db.session.commit()
        log_audit(current_user.id, "job_edit", "job", job.id, f"Edited {job.title}")
        flash("Job updated.", "success")
        return redirect(url_for("admin.jobs"))
    return render_template("admin/edit_job.html", form=form, job=job, settings=settings,
                           title="Edit Job")


@bp.route("/job/status/<int:job_id>/<status>", methods=["POST"])
@login_required
@admin_required
def job_status(job_id, status):
    job = Job.query.get_or_404(job_id)
    job.status = status
    db.session.commit()
    log_audit(current_user.id, "job_status", "job", job.id, f"Status -> {status}")
    # Notify employer
    create_notification(job.employer_id, "Job Status Updated",
                        f"Your job '{job.title}' is now: {status.title()}.",
                        link=url_for("employer.my_jobs"), ntype="job")
    flash(f"Job {status}.", "info")
    return redirect(url_for("admin.jobs"))


@bp.route("/job/feature/<int:job_id>", methods=["POST"])
@login_required
@admin_required
def job_feature(job_id):
    job = Job.query.get_or_404(job_id)
    job.is_featured = not job.is_featured
    db.session.commit()
    flash("Job featured status updated.", "info")
    return redirect(url_for("admin.jobs"))


@bp.route("/job/delete/<int:job_id>", methods=["POST"])
@login_required
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    log_audit(current_user.id, "job_delete", "job", job_id, f"Deleted {job.title}")
    flash("Job deleted.", "info")
    return redirect(url_for("admin.jobs"))


# ---------------- Categories ----------------
@bp.route("/categories")
@login_required
@admin_required
def categories():
    settings = get_site_settings()
    cats = Category.query.order_by(Category.sort_order).all()
    return render_template("admin/categories.html", categories=cats, settings=settings,
                           title="Categories")


@bp.route("/category/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_category():
    settings = get_site_settings()
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data.strip(), description=form.description.data,
                       icon=form.icon.data, is_active=form.is_active.data,
                       sort_order=form.sort_order.data or 0)
        db.session.add(cat)
        db.session.commit()
        flash("Category added.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, settings=settings,
                           title="Add Category")


@bp.route("/category/edit/<int:cat_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_category(cat_id):
    settings = get_site_settings()
    cat = Category.query.get_or_404(cat_id)
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        form.populate_obj(cat)
        db.session.commit()
        flash("Category updated.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, settings=settings,
                           title="Edit Category")


@bp.route("/category/delete/<int:cat_id>", methods=["POST"])
@login_required
@admin_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


# ---------------- Applications ----------------
@bp.route("/applications")
@login_required
@admin_required
def applications():
    settings = get_site_settings()
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip()
    query = Application.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Application.created_at.desc())
    pagination = query.paginate(page=page, per_page=Config.ADMIN_PER_PAGE, error_out=False)
    return render_template("admin/applications.html", applications=pagination.items,
                           pagination=pagination, settings=settings, title="Applications")


@bp.route("/application/<int:app_id>", methods=["GET", "POST"])
@login_required
@admin_required
def view_application(app_id):
    settings = get_site_settings()
    app = Application.query.get_or_404(app_id)
    form = ApplicationStatusForm(obj=app)
    if form.validate_on_submit():
        prev = app.status
        app.status = form.status.data
        app.internal_notes = form.internal_notes.data
        from datetime import datetime
        app.status_updated_at = datetime.utcnow()
        from models import ApplicationStatusHistory
        db.session.add(ApplicationStatusHistory(
            application_id=app.id, previous_status=prev, new_status=app.status,
            changed_by=current_user.id, note="Status updated by admin"))
        db.session.commit()
        create_notification(app.applicant_id, "Application Status Updated",
                            f"Your application for {app.job.title} is now: {app.status.title()}.",
                            link=url_for("seeker.applications"), ntype="application")
        flash("Application status updated.", "success")
        return redirect(url_for("admin.view_application", app_id=app.id))
    return render_template("admin/application_detail.html", app=app, form=form,
                           settings=settings, title="Application")


# ---------------- Messages ----------------
@bp.route("/messages")
@login_required
@admin_required
def messages():
    settings = get_site_settings()
    page = request.args.get("page", 1, type=int)
    read = request.args.get("read", "").strip()
    query = ContactMessage.query
    if read == "read":
        query = query.filter_by(is_read=True)
    elif read == "unread":
        query = query.filter_by(is_read=False)
    query = query.order_by(ContactMessage.created_at.desc())
    pagination = query.paginate(page=page, per_page=Config.ADMIN_PER_PAGE, error_out=False)
    return render_template("admin/messages.html", messages=pagination.items,
                           pagination=pagination, settings=settings, title="Messages")


@bp.route("/message/<int:msg_id>")
@login_required
@admin_required
def view_message(msg_id):
    settings = get_site_settings()
    msg = ContactMessage.query.get_or_404(msg_id)
    if not msg.is_read:
        msg.is_read = True
        db.session.commit()
    return render_template("admin/message_detail.html", msg=msg, settings=settings,
                           title="Message")


@bp.route("/message/toggle/<int:msg_id>", methods=["POST"])
@login_required
@admin_required
def toggle_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = not msg.is_read
    db.session.commit()
    return redirect(url_for("admin.messages"))


@bp.route("/message/delete/<int:msg_id>", methods=["POST"])
@login_required
@admin_required
def delete_message(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted.", "info")
    return redirect(url_for("admin.messages"))


# ---------------- Banners ----------------
@bp.route("/banners")
@login_required
@admin_required
def banners():
    settings = get_site_settings()
    items = Banner.query.order_by(Banner.sort_order).all()
    return render_template("admin/banners.html", banners=items, settings=settings,
                           title="Banners")


@bp.route("/banner/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_banner():
    settings = get_site_settings()
    form = BannerForm()
    if form.validate_on_submit():
        banner = Banner(title=form.title.data, subtitle=form.subtitle.data,
                        button_text=form.button_text.data, button_url=form.button_url.data,
                        is_active=form.is_active.data, sort_order=form.sort_order.data or 0)
        if form.image.data:
            banner.image = save_upload(form.image.data, "banners", Config.ALLOWED_BANNER_EXTENSIONS)
        db.session.add(banner)
        db.session.commit()
        flash("Banner added.", "success")
        return redirect(url_for("admin.banners"))
    return render_template("admin/banner_form.html", form=form, settings=settings,
                           title="Add Banner")


@bp.route("/banner/edit/<int:bid>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_banner(bid):
    settings = get_site_settings()
    banner = Banner.query.get_or_404(bid)
    form = BannerForm(obj=banner)
    if form.validate_on_submit():
        form.populate_obj(banner)
        if form.image.data:
            delete_upload(banner.image)
            banner.image = save_upload(form.image.data, "banners", Config.ALLOWED_BANNER_EXTENSIONS)
        db.session.commit()
        flash("Banner updated.", "success")
        return redirect(url_for("admin.banners"))
    return render_template("admin/banner_form.html", form=form, banner=banner,
                           settings=settings, title="Edit Banner")


@bp.route("/banner/delete/<int:bid>", methods=["POST"])
@login_required
@admin_required
def delete_banner(bid):
    banner = Banner.query.get_or_404(bid)
    delete_upload(banner.image)
    db.session.delete(banner)
    db.session.commit()
    flash("Banner deleted.", "info")
    return redirect(url_for("admin.banners"))


# ---------------- CMS / Settings ----------------
@bp.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    settings = get_site_settings()
    form = SiteSettingsForm(obj=settings)
    if form.validate_on_submit():
        old_logo = settings.logo
        old_favicon = settings.favicon
        old_footer = settings.footer_background
        form.populate_obj(settings)
        # Preserve existing files unless a new one is actually uploaded
        if form.logo.data and hasattr(form.logo.data, "filename") and form.logo.data.filename:
            delete_upload(old_logo)
            settings.logo = save_upload(form.logo.data, "logos", Config.ALLOWED_IMAGE_EXTENSIONS)
        else:
            settings.logo = old_logo
        if form.favicon.data and hasattr(form.favicon.data, "filename") and form.favicon.data.filename:
            delete_upload(old_favicon)
            settings.favicon = save_upload(form.favicon.data, "logos", Config.ALLOWED_IMAGE_EXTENSIONS)
        else:
            settings.favicon = old_favicon
        if form.footer_background.data and hasattr(form.footer_background.data, "filename") and form.footer_background.data.filename:
            delete_upload(old_footer)
            settings.footer_background = save_upload(form.footer_background.data, "banners", Config.ALLOWED_BANNER_EXTENSIONS)
        else:
            settings.footer_background = old_footer
        db.session.commit()
        log_audit(current_user.id, "settings_update", "site_settings", settings.id, "Updated site settings")
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", form=form, settings=settings, title="Website Settings")


@bp.route("/homepage", methods=["GET", "POST"])
@login_required
@admin_required
def homepage():
    settings = get_site_settings()
    form = HomepageForm(obj=settings)
    if form.validate_on_submit():
        old_hero = settings.hero_background
        form.populate_obj(settings)
        # Preserve existing hero banner unless a new one is actually uploaded
        if form.hero_background.data and hasattr(form.hero_background.data, "filename") and form.hero_background.data.filename:
            delete_upload(old_hero)
            settings.hero_background = save_upload(form.hero_background.data, "banners",
                                                   Config.ALLOWED_BANNER_EXTENSIONS)
        else:
            settings.hero_background = old_hero
        db.session.commit()
        log_audit(current_user.id, "homepage_update", "site_settings", settings.id, "Updated homepage CMS")
        flash("Homepage updated.", "success")
        return redirect(url_for("admin.homepage"))
    return render_template("admin/homepage.html", form=form, settings=settings, title="Homepage CMS")


@bp.route("/about", methods=["GET", "POST"])
@login_required
@admin_required
def about():
    settings = get_site_settings()
    form = AboutForm(obj=settings)
    if form.validate_on_submit():
        form.populate_obj(settings)
        db.session.commit()
        flash("About page updated.", "success")
        return redirect(url_for("admin.about"))
    return render_template("admin/about.html", form=form, settings=settings, title="About CMS")


@bp.route("/legal", methods=["GET", "POST"])
@login_required
@admin_required
def legal():
    settings = get_site_settings()
    form = LegalForm(obj=settings)
    if form.validate_on_submit():
        form.populate_obj(settings)
        db.session.commit()
        flash("Legal pages updated.", "success")
        return redirect(url_for("admin.legal"))
    return render_template("admin/legal.html", form=form, settings=settings, title="Legal Pages")


@bp.route("/maintenance", methods=["POST"])
@login_required
@admin_required
def maintenance():
    settings = get_site_settings()
    settings.maintenance_mode = not settings.maintenance_mode
    db.session.commit()
    flash("Maintenance mode " + ("enabled." if settings.maintenance_mode else "disabled."), "info")
    return redirect(url_for("admin.settings"))


@bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():
    settings = get_site_settings()
    page = request.args.get("page", 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=Config.ADMIN_PER_PAGE, error_out=False)
    return render_template("admin/audit_logs.html", logs=logs, settings=settings,
                           title="Audit Logs")


@bp.route("/notifications")
@login_required
@admin_required
def notifications():
    settings = get_site_settings()
    notes = current_user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template("admin/notifications.html", notes=notes, settings=settings,
                           title="Notifications")
