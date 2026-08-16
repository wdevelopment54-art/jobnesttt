# JobNest — Professional Online Job Portal

A complete, production-ready job portal built with **Flask**, **SQLite**, **Flask-SQLAlchemy**, **Jinja2**, and vanilla HTML/CSS/JS. No React/Vue/Angular, no external database required.

## Features

### Three Roles (full RBAC)
- **Job Seeker**: profile, resume upload (PDF/DOC/DOCX), education/experience/skills CRUD, job search & filters, save jobs, apply, track applications, notifications, profile completion %.
- **Employer**: company profile + logo, post/edit/delete jobs (draft/submit/close), view applicants, change application status, notifications.
- **Admin**: full CMS — users, companies, jobs (approve/reject/publish/suspend/feature), categories, applications, contact messages, banners, website settings (logo/favicon/name/social/contact), homepage CMS, about CMS, legal pages, maintenance mode, audit logs, dynamic statistics.

### Public Pages
Home, Jobs (search/filter/sort/paginate), Job Detail, Companies, Company Detail, About, Contact, Login, Register, Privacy, Terms, 404, 403, 500, Maintenance.

### Security
- Werkzeug password hashing
- CSRF protection on all forms
- Server-side validation
- Secure file uploads (extension/MIME/size checks, safe generated filenames)
- Private resume serving via authorized routes only
- `DEBUG=False` in production, secrets via `.env`

## Tech Stack
- Python 3.10+, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- SQLite (zero-config)
- Bootstrap 5.3 + Font Awesome 6 (CDN)
- Vanilla JS (ES6+)

## Setup

```bash
# 1. Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set a strong SECRET_KEY and admin credentials

# 4. Run
python wsgi.py
# or
flask run
```

The app auto-creates the SQLite database (`instance/job_portal.db`), seeds the admin account (from `.env`), default categories, and site settings on first run.

## Environment Variables (.env)
| Key | Description |
|-----|-------------|
| `SECRET_KEY` | Flask secret key (required) |
| `FLASK_ENV` | `development` or `production` (default `production`) |
| `ADMIN_NAME` | Default admin full name |
| `ADMIN_EMAIL` | Default admin email |
| `ADMIN_PASSWORD` | Default admin password |
| `MAIL_*` | Optional SMTP settings for password reset emails |

## Default Admin Login
After first run, log in with the `ADMIN_EMAIL` / `ADMIN_PASSWORD` from your `.env`.

## Project Structure
```
jobnest/
├── app.py                 # Application factory
├── wsgi.py                # WSGI entrypoint
├── config.py              # Configuration
├── extensions.py          # db, csrf
├── models/                # SQLAlchemy models (16)
├── forms/                 # WTForms
├── utils/                 # uploads, RBAC, notifications, audit
├── routes/                # blueprints (auth, public, seeker, employer, admin, errors)
├── templates/             # Jinja2 templates
├── static/                # css, js, uploads, images
└── requirements.txt
```

## Deployment
Use a WSGI server (gunicorn/waitress) with `wsgi:app`. Set `FLASK_ENV=production` and a strong `SECRET_KEY`. The app is fully self-contained with SQLite — no external services required.

## License
MIT
# jobnesttt  
