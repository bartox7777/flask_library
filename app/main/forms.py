from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    phrase = StringField("Wyszukaj książkę...", validators=[DataRequired()])
    submit = SubmitField("Szukaj")