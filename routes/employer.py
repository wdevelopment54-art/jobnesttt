from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user

from extensions import db
from models import (Company, Job, Category, Application, User, UserProfile, Resume,
                    Education, Experience, Skill, Notification)
from forms.company import CompanyForm
from forms.job import JobForm, ApplicationStatusForm
from utils import (employer_required, save_upload, delete_upload, create_notification,
                   get_site_settings, log_audit)
from config import Config

bp = Blueprint("employer", __name__, url_prefix="/employer")


@bp.route("/dashboard")
@login_required
@employer_required
def dashboard():
    settings = get_site_settings()
    company = current_user.company
    jobs = []
    apps = []
    stats = {}
    if company:
        jobs = company.jobs.order_by(Job.created_at.desc()).all()
        job_ids = [j.id for j in jobs]
        apps = Application.query.filter(Application.job_id.in_(job_ids)).all() if job_ids else []
        stats = {
            "total_jobs": len(jobs),
            "published": sum(1 for j in jobs if j.status == "published"),
            "pending": sum(1 for j in jobs if j.status in ("pending", "draft")),
            "total_apps": len(apps),
            "new_apps": sum(1 for a in apps if a.status == "pending"),
        }
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).limit(5).all()
    return render_template("employer/dashboard.html", settings=settings, company=company,
                           jobs=jobs, apps=apps, stats=stats, notifications=notifications,
                           title="Employer Dashboard")


@bp.route("/company", methods=["GET", "POST"])
@login_required
@employer_required
def company_profile():
    settings = get_site_settings()
    company = current_user.company
    form = CompanyForm(obj=company)
    if form.validate_on_submit():
        if not company:
            company = Company(employer_id=current_user.id)
            db.session.add(company)
        company.name = form.name.data.strip()
        company.industry = form.industry.data
        company.website = form.website.data
        company.email = form.email.data
        company.phone = form.phone.data
        company.location = form.location.data
        company.about = form.about.data
        company.company_size = form.company_size.data
        company.founded_year = form.founded_year.data
        company.facebook = form.facebook.data
        company.instagram = form.instagram.data
        company.linkedin = form.linkedin.data
        company.youtube = form.youtube.data
        company.twitter = form.twitter.data
        if form.logo.data:
            delete_upload(company.logo)
            company.logo = save_upload(form.logo.data, "logos", Config.ALLOWED_IMAGE_EXTENSIONS)
        db.session.commit()
        flash("Company profile saved. It will be reviewed by an admin.", "success")
        return redirect(url_for("employer.company_profile"))
    return render_template("employer/company.html", form=form, company=company,
                           settings=settings, title="Company Profile")


@bp.route("/post-job", methods=["GET", "POST"])
@login_required
@employer_required
def post_job():
    settings = get_site_settings()
    company = current_user.company
    if not company or company.status != "approved":
        flash("You must have an approved company profile to post jobs.", "warning")
        return redirect(url_for("employer.company_profile"))
    form = JobForm()
    form.category_id.choices = [(0, "Select Category")] + [
        (c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    form.company_id.choices = [(company.id, company.name)]
    if form.validate_on_submit():
        action = request.form.get("action", "submit")
        status = "pending" if action == "submit" else "draft"
        job = Job(
            employer_id=current_user.id,
            company_id=company.id,
            category_id=form.category_id.data or None,
            title=form.title.data.strip(),
            location=form.location.data,
            employment_type=form.employment_type.data,
            experience_level=form.experience_level.data,
            salary_min=form.salary_min.data,
            salary_max=form.salary_max.data,
            salary_type=form.salary_type.data,
            vacancies=form.vacancies.data or 1,
            application_deadline=form.application_deadline.data,
            description=form.description.data,
            responsibilities=form.responsibilities.data,
            requirements=form.requirements.data,
            skills=form.skills.data,
            benefits=form.benefits.data,
            is_featured=form.is_featured.data,
            status=status,
        )
        db.session.add(job)
        db.session.commit()
        # Notify admins
        for admin in User.query.filter_by(role="admin").all():
            create_notification(admin.id, "New Job Posted",
                                f"{company.name} posted: {job.title}",
                                link=url_for("admin.jobs"), ntype="job")
        flash("Job submitted for approval." if status == "pending" else "Draft saved.", "success")
        return redirect(url_for("employer.my_jobs"))
    return render_template("employer/post_job.html", form=form, settings=settings,
                           title="Post Job")


@bp.route("/my-jobs")
@login_required
@employer_required
def my_jobs():
    settings = get_site_settings()
    company = current_user.company
    jobs = company.jobs.order_by(Job.created_at.desc()).all() if company else []
    return render_template("employer/my_jobs.html", jobs=jobs, settings=settings,
                           title="My Jobs")


@bp.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
@login_required
@employer_required
def edit_job(job_id):
    settings = get_site_settings()
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        abort(403)
    form = JobForm(obj=job)
    form.category_id.choices = [(0, "Select Category")] + [
        (c.id, c.name) for c in Category.query.filter_by(is_active=True).all()]
    form.company_id.choices = [(job.company_id, job.company.name)]
    if request.method == "GET":
        form.category_id.data = job.category_id or 0
    if form.validate_on_submit():
        action = request.form.get("action", "submit")
        job.title = form.title.data.strip()
        job.category_id = form.category_id.data or None
        job.location = form.location.data
        job.employment_type = form.employment_type.data
        job.experience_level = form.experience_level.data
        job.salary_min = form.salary_min.data
        job.salary_max = form.salary_max.data
        job.salary_type = form.salary_type.data
        job.vacancies = form.vacancies.data or 1
        job.application_deadline = form.application_deadline.data
        job.description = form.description.data
        job.responsibilities = form.responsibilities.data
        job.requirements = form.requirements.data
        job.skills = form.skills.data
        job.benefits = form.benefits.data
        job.is_featured = form.is_featured.data
        if action == "submit" and job.status in ("draft", "rejected"):
            job.status = "pending"
        db.session.commit()
        flash("Job updated.", "success")
        return redirect(url_for("employer.my_jobs"))
    return render_template("employer/edit_job.html", form=form, job=job, settings=settings,
                           title="Edit Job")


@bp.route("/delete-job/<int:job_id>", methods=["POST"])
@login_required
@employer_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        abort(403)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "info")
    return redirect(url_for("employer.my_jobs"))


@bp.route("/close-job/<int:job_id>", methods=["POST"])
@login_required
@employer_required
def close_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        abort(403)
    job.status = "closed"
    db.session.commit()
    flash("Job closed.", "info")
    return redirect(url_for("employer.my_jobs"))


@bp.route("/applicants/<int:job_id>")
@login_required
@employer_required
def applicants(job_id):
    settings = get_site_settings()
    job = Job.query.get_or_404(job_id)
    if job.employer_id != current_user.id:
        abort(403)
    status_filter = request.args.get("status", "").strip()
    query = job.applications
    if status_filter:
        query = query.filter_by(status=status_filter)
    apps = query.order_by(Application.created_at.desc()).all()
    return render_template("employer/applicants.html", apps=apps, job=job, settings=settings,
                           status_filter=status_filter, title="Applicants")


@bp.route("/application/<int:app_id>", methods=["GET", "POST"])
@login_required
@employer_required
def view_application(app_id):
    settings = get_site_settings()
    app = Application.query.get_or_404(app_id)
    if app.employer_id != current_user.id:
        abort(403)
    form = ApplicationStatusForm(obj=app)
    if form.validate_on_submit():
        prev = app.status
        app.status = form.status.data
        app.internal_notes = form.internal_notes.data
        app.status_updated_at = db.func.now() if hasattr(db, "func") else None
        from datetime import datetime
        app.status_updated_at = datetime.utcnow()
        from models import ApplicationStatusHistory
        db.session.add(ApplicationStatusHistory(
            application_id=app.id, previous_status=prev, new_status=app.status,
            changed_by=current_user.id, note="Status updated by employer"))
        db.session.commit()
        # Notify applicant
        create_notification(app.applicant_id, "Application Status Updated",
                            f"Your application for {app.job.title} is now: {app.status.title()}.",
                            link=url_for("seeker.applications"), ntype="application")
        flash("Application status updated.", "success")
        return redirect(url_for("employer.view_application", app_id=app.id))
    return render_template("employer/application_detail.html", app=app, form=form,
                           settings=settings, title="Application")


@bp.route("/notifications")
@login_required
@employer_required
def notifications():
    settings = get_site_settings()
    notes = current_user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template("employer/notifications.html", notes=notes, settings=settings,
                           title="Notifications")
