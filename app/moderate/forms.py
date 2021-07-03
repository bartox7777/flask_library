from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import IntegerField
from wtforms import FileField
from wtforms import TextAreaField
from wtforms import SelectField
from wtforms.validators import DataRequired
from wtforms.validators import NumberRange

from ..models import Book


class AddBookForm(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired()])
    title = StringField("Tytuł", validators=[DataRequired()])
    category = SelectField()
    # category_add = StringField("Dodaj kategorię")
    description = TextAreaField("Opis")
    # author = None
    number_of_copies = IntegerField("Liczba kopii", validators=[DataRequired(), NumberRange(min=0)])
    cover = FileField("Okładka")
    # publisher = None
    pages = IntegerField("Stron", validators=[DataRequired(), NumberRange(min=0)])
    year = IntegerField("Rok wydania", validators=[DataRequired()])
    submit = SubmitField("Dodaj książkę")