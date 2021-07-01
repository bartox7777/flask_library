from flask_wtf import FlaskForm
from flask_wtf.recaptcha import validators
from wtforms import StringField
from wtforms import SubmitField
from wtforms import IntegerField
from wtforms import FileField
from wtforms import TextAreaField
from wtforms.validators import DataRequired


class AddBookForm(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired()])
    title = StringField("Tytuł", validators=[DataRequired()])
    # category = None
    description = TextAreaField("Opis")
    # author = None
    number_of_copies = IntegerField("Liczba kopii", validators=[DataRequired()])
    cover = FileField("Okładka")
    # publisher = None
    pages = IntegerField("Stron", validators=[DataRequired()])
    year = IntegerField("Rok wydania", validators=[DataRequired()])
    submit = SubmitField("Dodaj książkę")