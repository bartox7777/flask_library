from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField


class SearchForm(FlaskForm):
    phrase = StringField("Wyszukaj książkę...")
    submit = SubmitField("Szukaj")