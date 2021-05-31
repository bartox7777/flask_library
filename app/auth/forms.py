from flask_wtf import FlaskForm
from flask_wtf.recaptcha import validators
from wtforms.fields.html5 import EmailField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import Email


class LoginForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired(), InputRequired(), Email()])
    password = PasswordField("Hasło", validators=[DataRequired(), InputRequired()])
    submit = SubmitField("Zaloguj się")