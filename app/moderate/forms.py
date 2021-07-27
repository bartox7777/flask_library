from flask import request

import os
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import IntegerField
from wtforms import FileField
from wtforms import TextAreaField
from wtforms import SelectField
from wtforms.fields.core import BooleanField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import NumberRange
from wtforms.validators import ValidationError
from isbnlib import is_isbn10
from isbnlib import is_isbn13
from isbnlib import clean

from ..models import Role

class BookForm(FlaskForm):
    isbn = StringField("ISBN", validators=[DataRequired()])
    title = StringField("Tytuł", validators=[DataRequired()])
    category = SelectField(validate_choice=False)  # True makes error - incorrect choice
    add_category = StringField("Nowa kategoria")
    description = TextAreaField("Opis")
    author = SelectField(validate_choice=False)  # True makes error - incorrect choice
    add_author = StringField("Nowy autor")
    number_of_copies = IntegerField("Liczba kopii", validators=[NumberRange(min=0, max=10000)])
    cover = FileField("Okładka")
    publisher = SelectField(validate_choice=False)  # True makes error - incorrect choice
    add_publisher = StringField("Nowy wydawca")
    pages = IntegerField("Stron", validators=[NumberRange(min=0, max=10000)])
    year = IntegerField("Rok wydania", validators=[DataRequired(), NumberRange(max=datetime.now().year)])
    submit = SubmitField()

    def validate_cover(form, field):
        if request.files.get("cover"):
            image = request.files["cover"]

            extension = os.path.splitext(image.filename)
            if extension[-1].lower() not in ("jpg", "jpeg", "png"):
                raise ValidationError("Nieprawidłowy format pliku. Dozwolone rozszerzenia: .JPG, .JPEG, .PNG")

            image_read = image.stream.read()
            image.stream.seek(0)
            if len(image_read) > 16 * 1000 * 1000: # bytes
                raise ValidationError("Plik nie może być większy niż 16 MB.")

    def validate_isbn(form, field):
        isbn = clean(form.isbn.data)
        if not (is_isbn10(isbn) or is_isbn13(isbn)):
            raise ValidationError("Nieprawidłowy numer ISBN.")


class BorrowBookForm(FlaskForm):
    user_id = StringField("ID użytkownika")
    users = SelectField(validate_choice=False)
    submit = SubmitField()


class SearchUserForm(FlaskForm):
    phrase = StringField("Dane użytkownika")
    submit = SubmitField()


class UserForm(FlaskForm):
    name = StringField("Imię", validators=[DataRequired()])
    surname = StringField("Nazwisko", validators=[DataRequired()])
    phone_number = StringField("Numer telefonu")
    extended_city = StringField("Miejscowość i kod pocztowy")
    extended_street = StringField("Ulica i numer mieszkania")
    email = StringField("E-mail", validators=[Email()])
    activated = BooleanField("Konto aktywne")
    role = SelectField("Rola", validate_choice=False)
    submit = SubmitField()