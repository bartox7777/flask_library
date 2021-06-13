from flask_wtf import FlaskForm
from wtforms.fields.html5 import EmailField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Email


class LoginForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired(), Email()])
    password = PasswordField("Hasło", validators=[DataRequired()])
    submit = SubmitField("Zaloguj się")