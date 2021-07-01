from flask_wtf import FlaskForm
from wtforms.fields.html5 import SearchField
from wtforms import SubmitField
from wtforms import SelectField


class SearchForm(FlaskForm):
    phrase = SearchField("Wyszukaj książkę...")
    search_by = SelectField(
        choices=[
            ("phrase", "Szukaj po frazie"),
            ("title", "Tytuł"),
            ("category", "Gatunek"),
            ("author", "Autor"),
            ("publisher", "Wydawca")
        ],
        default=("phrase", "Szukaj po frazie"),
        validate_choice=False
    )
    submit = SubmitField("Szukaj")