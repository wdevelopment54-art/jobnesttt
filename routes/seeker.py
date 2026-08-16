from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user

from extensions import db
from models import (UserProfile, Resume, Education, Experience, Skill, Application,
                    SavedJob, Job, Notification, Company)
from forms.profile import (ProfileForm, ResumeForm, EducationForm, ExperienceForm, SkillForm)
from forms.job import ApplicationForm
from utils import (seeker_required, save_upload, delete_upload, create_notification,
                   get_site_settings)
from config import Config

bp = Blueprint("seeker", __name__, url_prefix="/seeker")


@bp.route("/dashboard")
@login_required
@seeker_required
def dashboard():
    settings = get_site_settings()
    profile = current_user.profile or UserProfile(user_id=current_user.id)
    if not current_user.profile:
        db.session.add(profile)
        db.session.commit()
    completion = profile.completion_percentage()
    apps = current_user.applications.all()
    counts = {
        "total": len(apps),
        "pending": sum(1 for a in apps if a.status == "pending"),
        "shortlisted": sum(1 for a in apps if a.status == "shortlisted"),
        "interview": sum(1 for a in apps if a.status == "interview"),
        "accepted": sum(1 for a in apps if a.status == "accepted"),
        "rejected": sum(1 for a in apps if a.status == "rejected"),
    }
    saved_count = current_user.saved_jobs.count()
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).limit(5).all()
    return render_template("seeker/dashboard.html", settings=settings, profile=profile,
                           completion=completion, counts=counts, saved_count=saved_count,
                           notifications=notifications, title="Dashboard")


@bp.route("/profile", methods=["GET", "POST"])
@login_required
@seeker_required
def profile():
    settings = get_site_settings()
    profile = current_user.profile or UserProfile(user_id=current_user.id)
    form = ProfileForm(obj=current_user if request.method == "GET" else None)
    if request.method == "GET":
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone
        if profile:
            form.city.data = profile.city
            form.country.data = profile.country
            form.professional_title.data = profile.professional_title
            form.about_me.data = profile.about_me
            form.linkedin.data = profile.linkedin
            form.portfolio.data = profile.portfolio
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data
        if not current_user.profile:
            profile = UserProfile(user_id=current_user.id)
            db.session.add(profile)
        profile.city = form.city.data
        profile.country = form.country.data
        profile.professional_title = form.professional_title.data
        profile.about_me = form.about_me.data
        profile.linkedin = form.linkedin.data
        profile.portfolio = form.portfolio.data
        if form.profile_photo.data:
            delete_upload(profile.profile_photo)
            path = save_upload(form.profile_photo.data, "photos", Config.ALLOWED_IMAGE_EXTENSIONS)
            profile.profile_photo = path
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("seeker.profile"))
    return render_template("seeker/profile.html", form=form, profile=profile,
                           settings=settings, title="My Profile")


@bp.route("/resume", methods=["GET", "POST"])
@login_required
@seeker_required
def resume():
    settings = get_site_settings()
    form = ResumeForm()
    if form.validate_on_submit():
        if form.resume.data:
            r = Resume(user_id=current_user.id,
                       original_filename=form.resume.data.filename,
                       file_size=0)
            db.session.add(r)
            db.session.flush()
            path = save_upload(form.resume.data, "resumes", Config.ALLOWED_RESUME_EXTENSIONS)
            r.filename = path
            import os
            r.file_size = os.path.getsize(os.path.join(Config.BASE_DIR, "static", path)) if path else 0
            # Set as current resume
            if not current_user.profile:
                current_user.profile = UserProfile(user_id=current_user.id)
            current_user.profile.current_resume_id = r.id
            db.session.commit()
            flash("Resume uploaded successfully.", "success")
            return redirect(url_for("seeker.resume"))
    resumes = current_user.resumes.order_by(Resume.uploaded_at.desc()).all()
    return render_template("seeker/resume.html", form=form, resumes=resumes,
                           settings=settings, title="My Resume")


@bp.route("/resume/delete/<int:resume_id>", methods=["POST"])
@login_required
@seeker_required
def delete_resume(resume_id):
    r = Resume.query.get_or_404(resume_id)
    if r.user_id != current_user.id:
        abort(403)
    delete_upload(r.filename)
    if current_user.profile and current_user.profile.current_resume_id == r.id:
        current_user.profile.current_resume_id = None
    db.session.delete(r)
    db.session.commit()
    flash("Resume deleted.", "info")
    return redirect(url_for("seeker.resume"))


@bp.route("/education", methods=["GET", "POST"])
@login_required
@seeker_required
def education():
    settings = get_site_settings()
    form = EducationForm()
    if form.validate_on_submit():
        edu = Education(
            user_id=current_user.id,
            institution=form.institution.data.strip(),
            degree=form.degree.data,
            field=form.field.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            description=form.description.data,
        )
        db.session.add(edu)
        db.session.commit()
        flash("Education added.", "success")
        return redirect(url_for("seeker.education"))
    items = current_user.educations.order_by(Education.start_date.desc()).all()
    return render_template("seeker/education.html", form=form, items=items,
                           settings=settings, title="Education")


@bp.route("/education/delete/<int:item_id>", methods=["POST"])
@login_required
@seeker_required
def delete_education(item_id):
    item = Education.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash("Education removed.", "info")
    return redirect(url_for("seeker.education"))


@bp.route("/experience", methods=["GET", "POST"])
@login_required
@seeker_required
def experience():
    settings = get_site_settings()
    form = ExperienceForm()
    if form.validate_on_submit():
        exp = Experience(
            user_id=current_user.id,
            company=form.company.data.strip(),
            position=form.position.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            current=(form.current.data == "yes"),
            description=form.description.data,
        )
        db.session.add(exp)
        db.session.commit()
        flash("Experience added.", "success")
        return redirect(url_for("seeker.experience"))
    items = current_user.experiences.order_by(Experience.start_date.desc()).all()
    return render_template("seeker/experience.html", form=form, items=items,
                           settings=settings, title="Experience")


@bp.route("/experience/delete/<int:item_id>", methods=["POST"])
@login_required
@seeker_required
def delete_experience(item_id):
    item = Experience.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash("Experience removed.", "info")
    return redirect(url_for("seeker.experience"))


@bp.route("/skills", methods=["GET", "POST"])
@login_required
@seeker_required
def skills():
    settings = get_site_settings()
    form = SkillForm()
    if form.validate_on_submit():
        skill = Skill(user_id=current_user.id, name=form.name.data.strip(),
                      level=form.level.data or "Beginner")
        db.session.add(skill)
        db.session.commit()
        flash("Skill added.", "success")
        return redirect(url_for("seeker.skills"))
    items = current_user.skills.order_by(Skill.name).all()
    return render_template("seeker/skills.html", form=form, items=items,
                           settings=settings, title="Skills")


@bp.route("/skills/delete/<int:item_id>", methods=["POST"])
@login_required
@seeker_required
def delete_skill(item_id):
    item = Skill.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash("Skill removed.", "info")
    return redirect(url_for("seeker.skills"))


@bp.route("/applications")
@login_required
@seeker_required
def applications():
    settings = get_site_settings()
    apps = current_user.applications.order_by(Application.created_at.desc()).all()
    return render_template("seeker/applications.html", apps=apps, settings=settings,
                           title="My Applications")


@bp.route("/saved-jobs")
@login_required
@seeker_required
def saved_jobs():
    settings = get_site_settings()
    saved = current_user.saved_jobs.order_by(SavedJob.created_at.desc()).all()
    return render_template("seeker/saved_jobs.html", saved=saved, settings=settings,
                           title="Saved Jobs")


@bp.route("/save-job/<int:job_id>", methods=["POST"])
@login_required
@seeker_required
def save_job(job_id):
    job = Job.query.get_or_404(job_id)
    existing = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if existing:
        db.session.delete(existing)
        flash("Job removed from saved list.", "info")
    else:
        db.session.add(SavedJob(user_id=current_user.id, job_id=job_id))
        flash("Job saved.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("public.jobs"))


@bp.route("/apply/<int:job_id>", methods=["GET", "POST"])
@login_required
@seeker_required
def apply(job_id):
    settings = get_site_settings()
    job = Job.query.get_or_404(job_id)
    if job.status != "published":
        abort(404)
    if job.is_expired:
        flash("The application deadline for this job has passed.", "warning")
        return redirect(url_for("public.job_detail", slug=job.slug))
    existing = Application.query.filter_by(applicant_id=current_user.id, job_id=job_id).first()
    if existing:
        flash("You have already applied for this job.", "info")
        return redirect(url_for("public.job_detail", slug=job.slug))
    form = ApplicationForm()
    if settings.require_cover_letter:
        from wtforms.validators import DataRequired
        form.cover_letter.validators = [DataRequired()]
    if form.validate_on_submit():
        resume = current_user.profile.current_resume_id if current_user.profile else None
        app = Application(
            job_id=job.id,
            applicant_id=current_user.id,
            employer_id=job.employer_id,
            resume_id=resume,
            cover_letter=form.cover_letter.data,
            status="pending",
        )
        db.session.add(app)
        db.session.flush()
        from models import ApplicationStatusHistory
        db.session.add(ApplicationStatusHistory(application_id=app.id,
                                                new_status="pending",
                                                changed_by=current_user.id,
                                                note="Application submitted"))
        db.session.commit()
        # Notify employer
        create_notification(job.employer_id, "New Application",
                            f"{current_user.full_name} applied for {job.title}.",
                            link=url_for("employer.applicants", job_id=job.id), ntype="application")
        flash("Your application has been submitted.", "success")
        return redirect(url_for("seeker.applications"))
    return render_template("seeker/apply.html", form=form, job=job, settings=settings,
                           title=f"Apply - {job.title}")


@bp.route("/notifications")
@login_required
def notifications():
    settings = get_site_settings()
    notes = current_user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template("seeker/notifications.html", notes=notes, settings=settings,
                           title="Notifications")


@bp.route("/notifications/mark-read/<int:note_id>", methods=["POST"])
@login_required
def mark_notification_read(note_id):
    note = Notification.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    note.is_read = True
    db.session.commit()
    return redirect(request.referrer or url_for("seeker.notifications"))


@bp.route("/notifications/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    current_user.notifications.update({Notification.is_read: True})
    db.session.commit()
    return redirect(request.referrer or url_for("seeker.notifications"))

@bp.route("/resume/<int:resume_id>")
@login_required
def view_resume(resume_id):
    import os
    from flask import send_from_directory
    r = Resume.query.get_or_404(resume_id)
    authorized = False
    if r.user_id == current_user.id:
        authorized = True
    elif current_user.is_admin:
        authorized = True
    elif current_user.is_employer and current_user.company:
        app = Application.query.filter_by(resume_id=resume_id, employer_id=current_user.id).first()
        if app:
            authorized = True
    if not authorized:
        abort(403)
    if not r.filename:
        abort(404)
    folder = os.path.join(Config.BASE_DIR, "static", os.path.dirname(r.filename))
    filename = os.path.basename(r.filename)
    return send_from_directory(folder, filename, as_attachment=True)


@bp.route("/candidate/<int:user_id>")
@login_required
def candidate_profile(user_id):
    settings = get_site_settings()
    user = User.query.get_or_404(user_id)
    if not user.is_seeker:
        abort(404)
    authorized = (user.id == current_user.id) or current_user.is_admin
    if not authorized and current_user.is_employer and current_user.company:
        app = Application.query.filter_by(applicant_id=user_id, employer_id=current_user.id).first()
        if app:
            authorized = True
    if not authorized:
        abort(403)
    profile = user.profile
    educations = user.educations.order_by(Education.start_date.desc()).all()
    experiences = user.experiences.order_by(Experience.start_date.desc()).all()
    skills = user.skills.all()
    return render_template("seeker/candidate_profile.html", user=user, profile=profile,
                           educations=educations, experiences=experiences, skills=skills,
                           settings=settings, title=f"{user.full_name} Profile")
