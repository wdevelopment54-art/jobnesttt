from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user

from extensions import db
from models import (Job, Company, Category, SiteSettings, ContactMessage, User,
                    Application, SavedJob)
from forms.company import ContactForm
from utils import get_site_settings, save_upload, create_notification
from config import Config

bp = Blueprint("public", __name__)


@bp.route("/")
def home():
    settings = get_site_settings()
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).limit(8).all()
    featured_jobs = []
    latest_jobs = []
    featured_companies = []
    stats = {}
    if settings.show_featured_jobs:
        featured_jobs = Job.query.filter_by(status="published", is_featured=True).order_by(Job.created_at.desc()).limit(6).all()
    if settings.show_latest_jobs:
        latest_jobs = Job.query.filter_by(status="published").order_by(Job.created_at.desc()).limit(8).all()
    if settings.show_featured_companies:
        featured_companies = Company.query.filter_by(status="approved", is_featured=True).limit(8).all()
    if settings.show_statistics:
        stats = {
            "jobs": Job.query.filter_by(status="published").count(),
            "companies": Company.query.filter_by(status="approved").count(),
            "seekers": User.query.filter_by(role="seeker").count(),
            "applications": Application.query.count(),
        }
    banners = None
    return render_template("home.html", settings=settings, categories=categories,
                           featured_jobs=featured_jobs, latest_jobs=latest_jobs,
                           featured_companies=featured_companies, stats=stats,
                           title=settings.browser_title)


@bp.route("/jobs")
def jobs():
    settings = get_site_settings()
    page = request.args.get("page", 1, type=int)
    keyword = request.args.get("keyword", "").strip()
    location = request.args.get("location", "").strip()
    category_id = request.args.get("category", type=int)
    employment_type = request.args.get("employment_type", "").strip()
    experience_level = request.args.get("experience_level", "").strip()
    sort = request.args.get("sort", "newest")

    query = Job.query.filter_by(status="published")
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            db.or_(Job.title.ilike(like), Job.description.ilike(like),
                   Job.skills.ilike(like), Job.location.ilike(like))
        )
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if employment_type:
        query = query.filter_by(employment_type=employment_type)
    if experience_level:
        query = query.filter_by(experience_level=experience_level)

    if sort == "oldest":
        query = query.order_by(Job.created_at.asc())
    elif sort == "salary":
        query = query.order_by(Job.salary_max.desc())
    else:
        query = query.order_by(Job.created_at.desc())

    pagination = query.paginate(page=page, per_page=Config.JOBS_PER_PAGE, error_out=False)
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    return render_template("jobs/jobs.html", jobs=pagination.items, pagination=pagination,
                           categories=categories, settings=settings, title="Browse Jobs")


@bp.route("/job/<slug>")
def job_detail(slug):
    settings = get_site_settings()
    job = Job.query.filter_by(slug=slug).first_or_404()
    if job.status != "published":
        abort(404)
    job.views += 1
    db.session.commit()

    saved = False
    applied = False
    if current_user.is_authenticated and current_user.is_seeker:
        saved = SavedJob.query.filter_by(user_id=current_user.id, job_id=job.id).first() is not None
        applied = Application.query.filter_by(applicant_id=current_user.id, job_id=job.id).first() is not None

    related = Job.query.filter_by(status="published", category_id=job.category_id)\
        .filter(Job.id != job.id).limit(4).all()
    return render_template("jobs/job_detail.html", job=job, settings=settings, saved=saved,
                           applied=applied, related=related, title=job.title)


@bp.route("/companies")
def companies():
    settings = get_site_settings()
    page = request.args.get("page", 1, type=int)
    keyword = request.args.get("keyword", "").strip()
    industry = request.args.get("industry", "").strip()
    query = Company.query.filter_by(status="approved")
    if keyword:
        query = query.filter(db.or_(Company.name.ilike(f"%{keyword}%"),
                                    Company.location.ilike(f"%{keyword}%")))
    if industry:
        query = query.filter(Company.industry.ilike(f"%{industry}%"))
    query = query.order_by(Company.is_featured.desc(), Company.created_at.desc())
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    industries = [i[0] for i in db.session.query(Company.industry).filter(
        Company.industry.isnot(None)).distinct().all()]
    return render_template("companies/companies.html", companies=pagination.items,
                           pagination=pagination, industries=industries, settings=settings,
                           title="Companies")


@bp.route("/company/<slug>")
def company_detail(slug):
    settings = get_site_settings()
    company = Company.query.filter_by(slug=slug).first_or_404()
    if company.status != "approved":
        abort(404)
    jobs = Job.query.filter_by(status="published", company_id=company.id)\
        .order_by(Job.created_at.desc()).all()
    return render_template("companies/company_detail.html", company=company, jobs=jobs,
                           settings=settings, title=company.name)


@bp.route("/about")
def about():
    settings = get_site_settings()
    stats = {
        "jobs": Job.query.filter_by(status="published").count(),
        "companies": Company.query.filter_by(status="approved").count(),
        "seekers": User.query.filter_by(role="seeker").count(),
        "applications": Application.query.count(),
    }
    values = [v.strip() for v in (settings.about_values or "").split(",") if v.strip()]
    return render_template("about.html", settings=settings, stats=stats, values=values,
                           title="About Us")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    settings = get_site_settings()
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=form.phone.data,
            subject=form.subject.data,
            message=form.message.data.strip(),
        )
        db.session.add(msg)
        db.session.commit()
        # Notify admins
        admins = User.query.filter_by(role="admin").all()
        for admin in admins:
            create_notification(admin.id, "New Contact Message",
                                f"Message from {msg.name}: {msg.subject or '(no subject)'}",
                                link=url_for("admin.messages"), ntype="message")
        flash("Thank you! Your message has been sent.", "success")
        return redirect(url_for("public.contact"))
    return render_template("contact.html", form=form, settings=settings, title="Contact Us")


@bp.route("/privacy")
def privacy():
    settings = get_site_settings()
    return render_template("legal/privacy.html", settings=settings, title="Privacy Policy")


@bp.route("/terms")
def terms():
    settings = get_site_settings()
    return render_template("legal/terms.html", settings=settings, title="Terms & Conditions")
