from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, URL, Email, Length


##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8)])
    submit_button = SubmitField(label="Sign Me Up!")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8)])
    submit_button = SubmitField(label="Let Me In!")


class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField(label="SUBMIT COMMENT")


class ContactForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    phone_number = IntegerField(label="Phone Number (optional)", )
    message = TextAreaField(label="Message", validators=[DataRequired()])
    submit = SubmitField(label="SEND")


class VerifyForm(FlaskForm):
    otp = StringField(label="Enter OTP", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField(label="VALIDATE")


class ForgetPassword(FlaskForm):
    email = StringField("Enter your Email", validators=[DataRequired(), Email()])
    submit = SubmitField(label="SEARCH ACCOUNT")


class NewPassword(FlaskForm):
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8)])
    submit = SubmitField(label="SEARCH ACCOUNT")
