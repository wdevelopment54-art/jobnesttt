from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, URL

from config import Config


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=150)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    profile_photo = FileField("Profile Photo", validators=[
        FileAllowed(Config.ALLOWED_IMAGE_EXTENSIONS, "Images only (jpg, png, webp, gif).")
    ])
    city = StringField("City", validators=[Optional(), Length(max=100)])
    country = StringField("Country", validators=[Optional(), Length(max=100)])
    professional_title = StringField("Professional Title", validators=[Optional(), Length(max=150)])
    about_me = TextAreaField("About Me", validators=[Optional(), Length(max=2000)])
    linkedin = URLField("LinkedIn", validators=[Optional(), URL()])
    portfolio = URLField("Portfolio", validators=[Optional(), URL()])
    submit = SubmitField("Save Profile")


class ResumeForm(FlaskForm):
    resume = FileField("Resume", validators=[
        FileAllowed(Config.ALLOWED_RESUME_EXTENSIONS, "PDF, DOC or DOCX only.")
    ])
    submit = SubmitField("Upload Resume")


class EducationForm(FlaskForm):
    institution = StringField("Institution", validators=[DataRequired(), Length(max=150)])
    degree = StringField("Degree", validators=[Optional(), Length(max=150)])
    field = StringField("Field of Study", validators=[Optional(), Length(max=150)])
    start_date = StringField("Start Date", validators=[Optional(), Length(max=20)], description="e.g. 2018")
    end_date = StringField("End Date", validators=[Optional(), Length(max=20)], description="e.g. 2022 or Present")
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save Education")


class ExperienceForm(FlaskForm):
    company = StringField("Company", validators=[DataRequired(), Length(max=150)])
    position = StringField("Position", validators=[Optional(), Length(max=150)])
    start_date = StringField("Start Date", validators=[Optional(), Length(max=20)])
    end_date = StringField("End Date", validators=[Optional(), Length(max=20)])
    current = StringField("Current Position", validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save Experience")


class SkillForm(FlaskForm):
    name = StringField("Skill", validators=[DataRequired(), Length(max=100)])
    level = StringField("Level", validators=[Optional(), Length(max=30)])
    submit = SubmitField("Add Skill")
