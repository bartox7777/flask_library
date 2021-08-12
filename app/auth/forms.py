from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms.fields.core import StringField
from wtforms.fields.html5 import EmailField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import EqualTo
from wtforms.validators import Email


class LoginForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Hasło", validators=[DataRequired()])
    submit = SubmitField("Zaloguj się")


class ChangePasswordForm(FlaskForm):
    password = PasswordField("Nowe hasło", validators=[DataRequired()])
    repeated_password = PasswordField("Powtórz nowe hasło", validators=[DataRequired(), EqualTo("password", "Hasła nie są takie same.")])
    submit = SubmitField("Zmień hasło")