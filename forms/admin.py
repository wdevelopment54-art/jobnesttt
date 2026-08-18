from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, TextAreaField, SubmitField, BooleanField, URLField,
                     IntegerField, SelectField)
from wtforms.validators import DataRequired, Length, Optional, URL, NumberRange
from forms.validators import SafeEmail

from config import Config


class CategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=500)])
    icon = StringField("Icon (FontAwesome class)", validators=[Optional(), Length(max=50)])
    is_active = BooleanField("Active")
    sort_order = IntegerField("Sort Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Category")


class BannerForm(FlaskForm):
    title = StringField("Title", validators=[Optional(), Length(max=200)])
    subtitle = StringField("Subtitle", validators=[Optional(), Length(max=300)])
    image = FileField("Image", validators=[
        FileAllowed(Config.ALLOWED_BANNER_EXTENSIONS, "Images only.")
    ])
    button_text = StringField("Button Text", validators=[Optional(), Length(max=100)])
    button_url = StringField("Button URL", validators=[Optional(), Length(max=255)])
    is_active = BooleanField("Active")
    sort_order = IntegerField("Sort Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Banner")


class SiteSettingsForm(FlaskForm):
    # Identity
    site_name = StringField("Website Name", validators=[DataRequired(), Length(max=150)])
    logo = FileField("Logo", validators=[FileAllowed(Config.ALLOWED_IMAGE_EXTENSIONS, "Images only.")])
    favicon = FileField("Favicon", validators=[FileAllowed(Config.ALLOWED_IMAGE_EXTENSIONS, "Images only.")])
    site_description = StringField("Site Description", validators=[Optional(), Length(max=300)])
    tagline = StringField("Tagline", validators=[Optional(), Length(max=200)])
    browser_title = StringField("Browser Title", validators=[Optional(), Length(max=150)])
    meta_description = TextAreaField("Meta Description", validators=[Optional(), Length(max=300)])

    # Contact
    contact_phone = StringField("Contact Phone", validators=[Optional(), Length(max=30)])
    contact_whatsapp = StringField("WhatsApp Number", validators=[Optional(), Length(max=30)])
    contact_email = StringField("Contact Email", validators=[Optional(), Length(max=150)])
    contact_address = StringField("Address", validators=[Optional(), Length(max=300)])
    business_hours = StringField("Business Hours", validators=[Optional(), Length(max=200)])

    # Social
    facebook = URLField("Facebook", validators=[Optional(), URL()])
    instagram = URLField("Instagram", validators=[Optional(), URL()])
    linkedin = URLField("LinkedIn", validators=[Optional(), URL()])
    youtube = URLField("YouTube", validators=[Optional(), URL()])
    twitter = URLField("Twitter", validators=[Optional(), URL()])

    # Footer
    footer_description = TextAreaField("Footer Description", validators=[Optional(), Length(max=400)])
    copyright_text = StringField("Copyright Text", validators=[Optional(), Length(max=200)])
    footer_background = FileField("Footer Background", validators=[FileAllowed(Config.ALLOWED_BANNER_EXTENSIONS, "Images only.")])

    submit = SubmitField("Save Settings")


class HomepageForm(FlaskForm):
    hero_title = StringField("Hero Title", validators=[Optional(), Length(max=200)])
    hero_subtitle = TextAreaField("Hero Subtitle", validators=[Optional(), Length(max=400)])
    hero_background = FileField("Hero Background", validators=[FileAllowed(Config.ALLOWED_BANNER_EXTENSIONS, "Images only.")])
    hero_cta_text = StringField("Hero CTA Text", validators=[Optional(), Length(max=100)])
    hero_cta_url = StringField("Hero CTA URL", validators=[Optional(), Length(max=255)])

    show_hero = BooleanField("Show Hero")
    show_featured_jobs = BooleanField("Show Featured Jobs")
    show_latest_jobs = BooleanField("Show Latest Jobs")
    show_categories = BooleanField("Show Categories")
    show_featured_companies = BooleanField("Show Featured Companies")
    show_statistics = BooleanField("Show Statistics")
    show_how_it_works = BooleanField("Show How It Works")
    show_cta = BooleanField("Show CTA")

    how_it_works_title = StringField("How It Works Title", validators=[Optional(), Length(max=150)])
    statistics_title = StringField("Statistics Title", validators=[Optional(), Length(max=150)])
    cta_title = StringField("CTA Title", validators=[Optional(), Length(max=150)])
    cta_subtitle = TextAreaField("CTA Subtitle", validators=[Optional(), Length(max=300)])

    submit = SubmitField("Save Homepage")


class AboutForm(FlaskForm):
    about_title = StringField("Title", validators=[Optional(), Length(max=200)])
    about_content = TextAreaField("Content", validators=[Optional()])
    about_mission = TextAreaField("Mission", validators=[Optional()])
    about_vision = TextAreaField("Vision", validators=[Optional()])
    about_banner = FileField("About Page Banner", validators=[
        FileAllowed(Config.ALLOWED_IMAGE_EXTENSIONS, "Images only.")
    ])
    submit = SubmitField("Save About Page")


class LegalForm(FlaskForm):
    privacy_title = StringField("Privacy Title", validators=[Optional(), Length(max=200)])
    privacy_content = TextAreaField("Privacy Content", validators=[Optional()])
    terms_title = StringField("Terms Title", validators=[Optional(), Length(max=200)])
    terms_content = TextAreaField("Terms Content", validators=[Optional()])
    submit = SubmitField("Save Legal Pages")


class UserEditForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    email = StringField("Email", validators=[DataRequired(), SafeEmail(), Length(max=150)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    role = SelectField("Role", choices=[
        ("seeker", "Job Seeker"), ("employer", "Employer"), ("admin", "Admin")
    ])
    is_active = BooleanField("Active")
    submit = SubmitField("Save User")
