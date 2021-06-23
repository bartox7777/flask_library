from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import SelectField
class SearchForm(FlaskForm):
    phrase = StringField("Wyszukaj książkę...")
    search_by = SelectField(choices=["Tytuł", "Gatunek", "Autor"])
    submit = SubmitField("Szukaj")