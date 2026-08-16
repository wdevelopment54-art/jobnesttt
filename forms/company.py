from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, URLField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, URL, NumberRange
from forms.validators import SafeEmail

from config import Config


class CompanyForm(FlaskForm):
    name = StringField("Company Name", validators=[DataRequired(), Length(max=150)])
    logo = FileField("Company Logo", validators=[
        FileAllowed(Config.ALLOWED_IMAGE_EXTENSIONS, "Images only.")
    ])
    industry = StringField("Industry", validators=[Optional(), Length(max=100)])
    website = URLField("Website", validators=[Optional(), URL()])
    email = StringField("Email", validators=[Optional(), Length(max=150)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    about = TextAreaField("About Company", validators=[Optional(), Length(max=3000)])
    company_size = StringField("Company Size", validators=[Optional(), Length(max=50)], description="e.g. 11-50")
    founded_year = IntegerField("Founded Year", validators=[Optional(), NumberRange(min=1800, max=2100)])
    facebook = URLField("Facebook", validators=[Optional(), URL()])
    instagram = URLField("Instagram", validators=[Optional(), URL()])
    linkedin = URLField("LinkedIn", validators=[Optional(), URL()])
    youtube = URLField("YouTube", validators=[Optional(), URL()])
    twitter = URLField("Twitter", validators=[Optional(), URL()])
    submit = SubmitField("Save Company")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), SafeEmail(), Length(max=150)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    subject = StringField("Subject", validators=[Optional(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=10, max=3000)])
    submit = SubmitField("Send Message")
