from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SubmitField, SelectField, IntegerField,
                     DateField, BooleanField)
from wtforms.validators import DataRequired, Length, Optional, NumberRange

EMPLOYMENT_TYPES = [
    ("full_time", "Full Time"),
    ("part_time", "Part Time"),
    ("contract", "Contract"),
    ("temporary", "Temporary"),
    ("internship", "Internship"),
    ("remote", "Remote"),
]
EXPERIENCE_LEVELS = [
    ("entry", "Entry Level"),
    ("junior", "Junior"),
    ("mid", "Mid Level"),
    ("senior", "Senior"),
    ("lead", "Lead / Manager"),
]
SALARY_TYPES = [
    ("monthly", "Per Month"),
    ("yearly", "Per Year"),
    ("hourly", "Per Hour"),
]


class JobForm(FlaskForm):
    title = StringField("Job Title", validators=[DataRequired(), Length(max=200)])
    category_id = SelectField("Category", coerce=int, validators=[Optional()])
    company_id = SelectField("Company", coerce=int, validators=[DataRequired()])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    employment_type = SelectField("Employment Type", choices=EMPLOYMENT_TYPES, default="full_time")
    experience_level = SelectField("Experience Level", choices=EXPERIENCE_LEVELS, default="mid")
    salary_min = IntegerField("Minimum Salary", validators=[Optional(), NumberRange(min=0)])
    salary_max = IntegerField("Maximum Salary", validators=[Optional(), NumberRange(min=0)])
    salary_type = SelectField("Salary Type", choices=SALARY_TYPES, default="monthly")
    vacancies = IntegerField("Vacancies", validators=[Optional(), NumberRange(min=1)], default=1)
    application_deadline = DateField("Application Deadline", validators=[Optional()])
    description = TextAreaField("Job Description", validators=[DataRequired(), Length(min=20)])
    responsibilities = TextAreaField("Responsibilities", validators=[Optional()])
    requirements = TextAreaField("Requirements", validators=[Optional()])
    skills = TextAreaField("Skills", validators=[Optional()], description="Comma separated")
    benefits = TextAreaField("Benefits", validators=[Optional()])
    is_featured = BooleanField("Feature this job")
    submit = SubmitField("Save Job")


class ApplicationForm(FlaskForm):
    cover_letter = TextAreaField("Cover Letter", validators=[Optional(), Length(max=3000)])
    submit = SubmitField("Submit Application")


class ApplicationStatusForm(FlaskForm):
    status = SelectField("Status", choices=[
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("shortlisted", "Shortlisted"),
        ("interview", "Interview"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ])
    internal_notes = TextAreaField("Internal Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Update Status")
