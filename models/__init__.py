"""Database models for the Job Portal application."""

from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from extensions import db


def slugify(text):
    import re
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "item"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="seeker")  # seeker, employer, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = db.relationship("UserProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    company = db.relationship("Company", backref="employer", uselist=False, cascade="all, delete-orphan")
    jobs = db.relationship("Job", backref="employer", lazy="dynamic", cascade="all, delete-orphan")
    applications = db.relationship("Application", backref="applicant", lazy="dynamic",
                                   foreign_keys="Application.applicant_id", cascade="all, delete-orphan")
    saved_jobs = db.relationship("SavedJob", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    educations = db.relationship("Education", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    experiences = db.relationship("Experience", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    skills = db.relationship("Skill", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    resumes = db.relationship("Resume", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    audit_logs = db.relationship("AuditLog", backref="admin", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_employer(self):
        return self.role == "employer"

    @property
    def is_seeker(self):
        return self.role == "seeker"

    def __repr__(self):
        return f"<User {self.email}>"


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    professional_title = db.Column(db.String(150), nullable=True)
    about_me = db.Column(db.Text, nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    portfolio = db.Column(db.String(255), nullable=True)
    current_resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    current_resume = db.relationship("Resume", foreign_keys=[current_resume_id])

    def completion_percentage(self):
        fields = [
            self.profile_photo, self.city, self.country, self.professional_title,
            self.about_me, self.linkedin, self.portfolio,
        ]
        total = len(fields) + 4  # + education, experience, skills, resume
        filled = sum(1 for f in fields if f)
        if self.current_resume_id:
            filled += 1
        if self.educations_count():
            filled += 1
        if self.experiences_count():
            filled += 1
        if self.skills_count():
            filled += 1
        return int((filled / total) * 100)

    def educations_count(self):
        return self.user.educations.count()

    def experiences_count(self):
        return self.user.experiences.count()

    def skills_count(self):
        return self.user.skills.count()


class Resume(db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Education(db.Model):
    __tablename__ = "education"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    institution = db.Column(db.String(150), nullable=False)
    degree = db.Column(db.String(150), nullable=True)
    field = db.Column(db.String(150), nullable=True)
    start_date = db.Column(db.String(20), nullable=True)
    end_date = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Experience(db.Model):
    __tablename__ = "experience"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    position = db.Column(db.String(150), nullable=True)
    start_date = db.Column(db.String(20), nullable=True)
    end_date = db.Column(db.String(20), nullable=True)
    current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(30), nullable=True, default="Beginner")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False)
    logo = db.Column(db.String(255), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    about = db.Column(db.Text, nullable=True)
    company_size = db.Column(db.String(50), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    facebook = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(255), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    youtube = db.Column(db.String(255), nullable=True)
    twitter = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending, approved, suspended
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs = db.relationship("Job", backref="company", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def is_approved(self):
        return self.status == "approved"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.slug and self.name:
            self.slug = self._make_slug()

    def _make_slug(self):
        base = slugify(self.name)
        unique = base
        n = 1
        while Company.query.filter_by(slug=unique).first():
            unique = f"{base}-{n}"
            n += 1
        return unique


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(50), nullable=True, default="briefcase")
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobs = db.relationship("Job", backref="category", lazy="dynamic")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.slug and self.name:
            self.slug = slugify(self.name)


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(230), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsibilities = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    benefits = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=True)
    salary_min = db.Column(db.Integer, nullable=True)
    salary_max = db.Column(db.Integer, nullable=True)
    salary_type = db.Column(db.String(20), default="monthly")  # monthly, yearly, hourly
    employment_type = db.Column(db.String(30), default="full_time")
    experience_level = db.Column(db.String(30), default="mid")
    vacancies = db.Column(db.Integer, default=1)
    application_deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="draft")  # draft, pending, approved, published, rejected, closed, expired, suspended
    is_featured = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = db.relationship("Application", backref="job", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def is_public(self):
        return self.status == "published"

    @property
    def is_expired(self):
        if self.application_deadline:
            return self.application_deadline < date.today()
        return False

    @property
    def can_apply(self):
        return self.status == "published" and not self.is_expired

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.slug and self.title:
            self.slug = self._make_slug()

    def _make_slug(self):
        base = slugify(self.title)
        unique = f"{base}-{self.employer_id or 0}"
        n = 1
        while Job.query.filter_by(slug=unique).first():
            unique = f"{base}-{self.employer_id or 0}-{n}"
            n += 1
        return unique


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.id"), nullable=True)
    cover_letter = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending, reviewed, shortlisted, interview, accepted, rejected
    internal_notes = db.Column(db.Text, nullable=True)
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resume = db.relationship("Resume")
    history = db.relationship("ApplicationStatusHistory", backref="application", lazy="dynamic",
                              cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("job_id", "applicant_id", name="uq_job_applicant"),)


class ApplicationStatusHistory(db.Model):
    __tablename__ = "application_status_history"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    previous_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SavedJob(db.Model):
    __tablename__ = "saved_jobs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", backref="saved_by")
    __table_args__ = (db.UniqueConstraint("user_id", "job_id", name="uq_user_job"),)


class Banner(db.Model):
    __tablename__ = "banners"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    subtitle = db.Column(db.String(300), nullable=True)
    image = db.Column(db.String(255), nullable=True)
    button_text = db.Column(db.String(100), nullable=True)
    button_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteSettings(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)

    # Identity
    site_name = db.Column(db.String(150), default="JobNest")
    logo = db.Column(db.String(255), nullable=True, default="logos/jobnest_logo-removebg-preview.png")
    favicon = db.Column(db.String(255), nullable=True, default="images/favicon.ico")
    site_description = db.Column(db.String(300), default="Find your dream job with JobNest.")
    tagline = db.Column(db.String(200), nullable=True)
    browser_title = db.Column(db.String(150), default="JobNest - Find Your Dream Job")
    meta_description = db.Column(db.String(300), default="JobNest is a professional job portal connecting job seekers with employers.")

    # Contact
    contact_phone = db.Column(db.String(30), default="03096890020")
    contact_whatsapp = db.Column(db.String(30), default="+923096890020")
    contact_email = db.Column(db.String(150), default="")
    contact_address = db.Column(db.String(300), default="")
    business_hours = db.Column(db.String(200), default="Mon - Fri: 9:00 AM - 6:00 PM")

    # Social
    facebook = db.Column(db.String(255), nullable=True)
    instagram = db.Column(db.String(255), nullable=True)
    linkedin = db.Column(db.String(255), nullable=True)
    youtube = db.Column(db.String(255), nullable=True)
    twitter = db.Column(db.String(255), nullable=True)

    # Footer
    footer_description = db.Column(db.String(400), default="JobNest connects talented professionals with great companies.")
    copyright_text = db.Column(db.String(200), default="© 2024 JobNest. All rights reserved.")
    footer_background = db.Column(db.String(255), nullable=True, default="banners/footer banner.webp")

    # Homepage CMS
    hero_title = db.Column(db.String(200), default="Find Your Dream Job")
    hero_subtitle = db.Column(db.String(400), default="Discover thousands of job opportunities with all the information you need. Its your future.")
    hero_background = db.Column(db.String(255), nullable=True, default="uploads/banners/header banner.webp")
    hero_cta_text = db.Column(db.String(100), default="Browse Jobs")
    hero_cta_url = db.Column(db.String(255), default="/jobs")
    hero_cta2_text = db.Column(db.String(100), default="Post a Job")
    hero_cta2_url = db.Column(db.String(255), default="/employer/post-job")

    show_hero = db.Column(db.Boolean, default=True)
    show_featured_jobs = db.Column(db.Boolean, default=True)
    show_latest_jobs = db.Column(db.Boolean, default=True)
    show_categories = db.Column(db.Boolean, default=True)
    show_featured_companies = db.Column(db.Boolean, default=True)
    show_statistics = db.Column(db.Boolean, default=True)
    show_how_it_works = db.Column(db.Boolean, default=True)
    show_cta = db.Column(db.Boolean, default=True)

    featured_jobs_heading = db.Column(db.String(150), default="Featured Jobs")
    featured_jobs_subheading = db.Column(db.String(250), default="Hand-picked opportunities from top employers.")
    latest_jobs_heading = db.Column(db.String(150), default="Latest Jobs")
    latest_jobs_subheading = db.Column(db.String(250), default="Recently posted job openings.")
    categories_heading = db.Column(db.String(150), default="Popular Categories")
    categories_subheading = db.Column(db.String(250), default="Browse jobs by category.")
    featured_companies_heading = db.Column(db.String(150), default="Featured Companies")
    featured_companies_subheading = db.Column(db.String(250), default="Trusted by leading organizations.")
    statistics_title = db.Column(db.String(150), default="Our Platform in Numbers")
    statistics_subheading = db.Column(db.String(250), default="Join thousands of professionals and companies.")

    cta_seeker_heading = db.Column(db.String(150), default="Are You a Job Seeker?")
    cta_seeker_text = db.Column(db.String(300), default="Create a free account, build your profile and apply to thousands of jobs.")
    cta_seeker_button = db.Column(db.String(100), default="Register as Job Seeker")
    cta_seeker_url = db.Column(db.String(255), default="/register")
    cta_employer_heading = db.Column(db.String(150), default="Are You an Employer?")
    cta_employer_text = db.Column(db.String(300), default="Post your jobs and find the best candidates for your company.")
    cta_employer_button = db.Column(db.String(100), default="Register as Employer")
    cta_employer_url = db.Column(db.String(255), default="/register")

    # About CMS
    about_title = db.Column(db.String(200), default="About JobNest")
    about_content = db.Column(db.Text, default="JobNest is a modern recruitment platform built to connect talented professionals with forward-thinking companies.")
    about_mission = db.Column(db.Text, default="To make meaningful employment accessible to everyone through smart, simple technology.")
    about_vision = db.Column(db.Text, default="To become the most trusted job portal for seekers and employers worldwide.")
    about_values = db.Column(db.Text, default="Integrity, Transparency, Innovation, Excellence")
    about_why_choose = db.Column(db.Text, default="We focus on real outcomes, verified employers and a seamless experience for everyone.")
    about_cta_heading = db.Column(db.String(150), default="Ready to get started?")
    about_cta_text = db.Column(db.String(300), default="Join JobNest today and take the next step in your career or hiring journey.")
    about_cta_button = db.Column(db.String(100), default="Get Started")
    about_cta_url = db.Column(db.String(255), default="/register")

    # Legal
    privacy_content = db.Column(db.Text, default="Our privacy policy will appear here.")
    terms_content = db.Column(db.Text, default="Our terms and conditions will appear here.")

    # Behavior
    require_cover_letter = db.Column(db.Boolean, default=False)
    maintenance_mode = db.Column(db.Boolean, default=False)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(50), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
