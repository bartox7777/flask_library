from flask import request

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import IntegerField
from wtforms import FileField
from wtforms import TextAreaField
from wtforms import SelectField
from wtforms.validators import DataRequired
from wtforms.validators import NumberRange
from wtforms.validators import ValidationError
from isbnlib import is_isbn10
from isbnlib import is_isbn13
from isbnlib import clean


class AddBookForm(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired()])
    title = StringField("Tytuł", validators=[DataRequired()])
    category = SelectField(validate_choice=False)  # True makes error - incorrect choice
    add_category = StringField("Nowa kategoria")
    description = TextAreaField("Opis")
    author = SelectField(validate_choice=False)  # True makes error - incorrect choice
    add_author = StringField("Nowy autor")
    number_of_copies = IntegerField("Liczba kopii", validators=[NumberRange(min=0)])
    cover = FileField("Okładka")
    publisher = SelectField(validate_choice=False)  # True makes error - incorrect choice
    pages = IntegerField("Stron", validators=[NumberRange(min=0)])
    year = StringField("Rok wydania", validators=[DataRequired()])
    submit = SubmitField("Dodaj książkę")

    def validate_cover(form, field):
        if request.files["cover"]:
            image = request.files["cover"]

            extension = image.filename.split(".")
            if extension[-1].lower() not in ("jpg", "jpeg", "png"):
                raise ValidationError("Nieprawidłowy format pliku. Dozwolone rozszerzenia: .JPG, .JPEG, .PNG")

            #TODO: call image.stream.read() makes this method in views return b''
            # if len(image.stream.read()) > 16 * 1000 * 1000: # bytes
            #     raise ValidationError("Plik nie może być większy niż 16 MB.")

    def validate_isbn(form, field):
        isbn = clean(form.isbn.data)
        if not (is_isbn10(isbn) or is_isbn13(isbn)):
            raise ValidationError("Nieprawidłowy numer ISBN.")
