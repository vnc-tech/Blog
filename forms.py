from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, EmailField, PasswordField, DateField
from wtforms.validators import DataRequired, URL, Optional, EqualTo
from flask_ckeditor import CKEditorField


class RegiterForm(FlaskForm):
    """Adding a user to the database"""
    height = "6vh"
    width = "10vw"
    email = EmailField("Email", validators=[DataRequired()], render_kw={
                       "style": f"height:{height}"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={
                             "style": f"height:{height}"})
    first_name = StringField("First Name", validators=[DataRequired()], render_kw={
        "autofocus": True, "style": f"height:{height}"})
    last_name = StringField("Last Name", validators=[DataRequired()], render_kw={
        "style": f"height:{height}"})
    birth_date = DateField("Birth Date", validators=[DataRequired()], render_kw={
        "style": f"height:{height}"})
    submit = SubmitField("Sign up", render_kw={
                         "style": "height:6vh; width:5vw"})


class AddPost(FlaskForm):
    """Adding Post Form"""
    height = "10vh"
    width = "20vh"
    blog_title = StringField("Post Title", validators=[DataRequired()], render_kw={
                             "autofocus": True, "style": f"height:{height}"})
    blog_subtitle = StringField("Subtitle (Optional)", validators=[Optional(
        strip_whitespace=True)], render_kw={"style": f"height:{height}"})
    blog_author = StringField("Author", validators=[DataRequired()], render_kw={
                              "style": f"height:{height}"})
    blog_img_url = URLField("Blog Image Url", validators=[
                            URL(), DataRequired()], render_kw={"style": f"height:{height}"})
    source_link = URLField("Source Link (Optional)", validators=[
                           Optional(), URL()], render_kw={"style": f"height:{height}"})
    blog_content = CKEditorField("Body", validators=[DataRequired()], render_kw={
                                 "style": "min-height:60vh"})
    submit = SubmitField("Submit Post", render_kw={
                         "style": f"height:{height}; min-width:15vw"})


class CommentForm(FlaskForm):
    """Add comments from the user"""
    text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit", render_kw={
                         "style": "height:6vh; min-width:5vw"})


class LoginForm(FlaskForm):
    """Login Form"""
    height = "6vh"
    width = "10vw"
    email = EmailField("Email", validators=[DataRequired()], render_kw={
        "autofocus": True, "style": f"height:{height}"})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={
                             "style": f"height:{height}"})
    submit = SubmitField("Login", render_kw={
                         "style": "height:6vh; min-width:5vw"})


class ChangePassword(FlaskForm):
    """Change Password"""
    height = "6vh"
    width = "10vw"
    current_password = PasswordField("Current Password", validators=[DataRequired()], render_kw={
        "autofocus": True, "style": f"height:{height}"})
    new_password = PasswordField("New Password", validators=[DataRequired()], render_kw={
        "style": f"height:{height}"})
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("new_password", message="Confirm Password should match New Password")], render_kw={
        "style": f"height:{height}"})
    submit = SubmitField("Submit", render_kw={
                         "style": "height:6vh; min-width:5vw"})


class ChangeUsername(FlaskForm):
    """Change Username"""
    # TODO: Create a Change Username form
    pass
