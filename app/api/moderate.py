import base64
from io import BytesIO
from flask import flash
from flask import abort
from flask import request
from flask import url_for
from flask import redirect
from flask import current_app
from flask import render_template
from flask import get_flashed_messages

import random
import string
import datetime
from isbnlib import clean
from isbnlib import desc
from isbnlib import meta
from isbnlib import is_isbn10
from isbnlib import is_isbn13
from sqlalchemy import or_
from flask_mail import Message
from flask_login import current_user

from .. import db
from .. import mail

from ..models import Book
from ..models import PersonalData
from ..models import User
from ..models import Author
from ..models import Borrow
from ..models import Role
from ..models import Permission

from . import api
from .main import dict_book
from .main import process_covers
from .decorators import moderator_required_api
from .decorators import admin_required_api


def dict_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role.name if user.role else None,
        "activated": user.activated,
        "name": user.personal_data[0].name,
        "surname": user.personal_data[0].surname,
        "phone_number": user.personal_data[0].phone_number,
        "extended_city": user.personal_data[0].extended_city,
        "extended_street": user.personal_data[0].extended_street,
    }


# ADDING


@api.route("/add-book", methods=("GET", "POST", "PUT"))
@moderator_required_api
def add_book():
    title = request.args.get("title")
    year = request.args.get("year")
    description = request.args.get("description")

    authors = [(author.id, author.full_name) for author in Author.query.all()]
    categories = [
        category[0] for category in db.session.query(Book.category).distinct().all()
    ]
    publishers = [
        publisher[0] for publisher in db.session.query(Book.publisher).distinct().all()
    ]

    if request.method == "PUT":
        category = (
            request.args.get("add_category")
            if request.args.get("add_category")
            else request.args.get("category")
        )
        publisher = (
            request.args.get("add_publisher")
            if request.args.get("add_publisher")
            else request.args.get("publisher")
        )

        author_id = request.args.get("author")
        if request.args.get("add_author"):
            new_author = Author(full_name=request.args.get("add_author"))
            db.session.add(new_author)
            db.session.commit()
            author_id = new_author.id

        new_book = Book(
            isbn=clean(request.args.get("isbn")),
            title=request.args.get("title"),
            category=category,
            description=request.args.get("description"),
            author_id=author_id,
            number_of_copies=request.args.get("number_of_copies"),
            cover=(
                request.files["cover"].stream.read()
                if request.files.get("cover")
                else None
            ),
            publisher=publisher,
            pages=request.args.get("pages"),
            year=request.args.get("year"),
        )

        db.session.add(new_book)
        db.session.commit()
        return {"book_id": new_book.id}
    elif request.method == "POST" and request.args.get("isbn"):
        print("POST")
        isbn = clean(request.args.get("isbn"))
        if is_isbn10(isbn) or is_isbn13(isbn):
            book_info = meta(isbn)
        else:
            book_info = dict()

        return {
            "title": book_info.get("Title"),
            "year": book_info.get("Year"),
            "description": desc(isbn),
            "categories": categories,
            "author": (
                book_info.get("Authors")[0] if book_info.get("Authors") else None
            ),
            "publisher": (
                book_info.get("Publisher") if book_info.get("Publisher") else None
            ),
        }

    return {
        "title": title,
        "year": year,
        "description": description,
        "categories": categories,
        "authors": authors,
        "publishers": publishers,
    }


@api.route("/add-user", methods=("GET", "PUT"))
@moderator_required_api
def add_user():
    roles = [(role.id, role.name) for role in Role.query.all()]
    role_user_id = Role.query.filter_by(name="user").first().id

    if request.method == "PUT":
        error = False
        if User.query.filter_by(email=request.args.get("email")).first():
            flash("Ten email jest już przypisany.", "danger")
            error = True
        if PersonalData.query.filter_by(
            phone_number=request.args.get("phone_number")
        ).first():
            flash("Ten numer telefonu jest już przypisany.", "danger")
            error = True

        if not error:
            password = "".join(
                random.choices(string.ascii_letters + string.digits, k=8)
            )

            new_user = User(
                email=request.args.get("email"),
                role_id=request.args.get("role"),
                password=password,
            )
            db.session.add(new_user)
            db.session.commit()

            new_user_personal_data = PersonalData(
                name=request.args.get("name"),
                surname=request.args.get("surname"),
                phone_number=request.args.get("phone_number"),
                extended_city=request.args.get("extended_city"),
                extended_street=request.args.get("extended_street"),
                user_id=new_user.id,
            )
            db.session.add(new_user_personal_data)
            db.session.commit()

            message = Message(
                subject="[LIBsys] - hasło do konta",
                recipients=[new_user.email],
                html=render_template(
                    "email/password.html", user=new_user, password=password
                ),
            )
            mail.send(message)
            flash(f"Użytkownik { new_user.full_name } dodany pomyślnie.", "success")
            flash(f"Hasło zostało wysłane na podanego e-maila.", "info")
            return {
                "user_id": new_user.id,
                "flashes": get_flashed_messages(with_categories=True)(
                    with_categories=True
                ),
            }

    return {
        "roles": roles,
        "role_user_id": role_user_id,
        "flashes": get_flashed_messages(with_categories=True),
    }


# EDITING


@api.route("/edit-book/<int:book_id>", methods=("GET", "PATCH"))
@moderator_required_api
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == "PATCH":
        book.isbn = request.args.get("isbn")
        book.title = request.args.get("title")
        book.category = request.args.get("category")
        book.description = request.args.get("description")
        book.author_id = request.args.get("author")
        book.number_of_copies = request.args.get("number_of_copies")
        book.publisher = request.args.get("publisher")
        book.pages = request.args.get("pages")
        book.year = request.args.get("year")
        base64_cover = request.args.get("cover")
        book.cover = BytesIO(base64.b64decode(base64_cover)).read()

        Author.query.get_or_404(book.author_id)

        db.session.commit()

        flash("Edycja książki przebiegła pomyślnie.", "success")
        return {
            "flashes": get_flashed_messages(with_categories=True),
            "book_id": book.id,
        }

    authors = [(author.id, author.full_name) for author in Author.query.all()]
    categories = [
        category[0] for category in db.session.query(Book.category).distinct().all()
    ]
    publishers = [
        publisher[0] for publisher in db.session.query(Book.publisher).distinct().all()
    ]

    return {
        "book": [dict_book(book, cover) for book, cover in process_covers([book])][0],
        "authors": authors,
        "categories": categories,
        "publishers": publishers,
        "flashes": get_flashed_messages(with_categories=True),
    }


@api.route("/edit-user/<int:user_id>", methods=("GET", "PATCH"))
@moderator_required_api
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    roles = [(role.id, role.name) for role in Role.query.filter_by()]

    if request.method == "PATCH":
        error = False
        user_by_email = User.query.filter_by(email=request.args.get("email")).first()
        personal_data_by_number = PersonalData.query.filter_by(
            phone_number=request.args.get("phone_number")
        ).first()
        if user_by_email and user_by_email is not user:
            flash("Ten email jest już przypisany.", "danger")
            error = True
        if (
            personal_data_by_number
            and personal_data_by_number is not user.personal_data[0]
        ):
            flash("Ten numer telefonu jest już przypisany.", "danger")
            error = True

        if error:
            return {
                "flashes": get_flashed_messages(with_categories=True)(
                    with_categories=True
                ),
                "user": dict_user(user),
                "roles": roles,
            }

        user.personal_data[0].name = request.args.get("name")
        user.personal_data[0].surname = request.args.get("surname")
        user.personal_data[0].phone_number = request.args.get("phone_number")
        user.personal_data[0].extended_city = request.args.get("extended_city")
        user.personal_data[0].extended_street = request.args.get("extended_street")
        user.email = request.args.get("email")
        user.role_id = request.args.get("role")
        user.activated = bool(int(request.args.get("activated")))
        db.session.commit()

        flash("Pomyślnie zedytowano dane.", "success")

    return {
        "user": dict_user(user),
        "roles": roles,
        "flashes": get_flashed_messages(with_categories=True),
    }


# ACTIONS


@api.route("/borrow-book/<int:book_id>", methods=("GET", "PUT"))
@moderator_required_api
def borrow_book(book_id):
    users = [(user.id, f"{user.full_name} ({ user.id })") for user in User.query.all()]
    book = Book.query.get_or_404(book_id)
    borrows = [borrow for borrow in book.borrows if borrow.return_date is None]
    if len(borrows) >= book.number_of_copies:
        flash("Brak dostępnych kopii do wypożyczenia.", "danger")
        return {
            "book_id": book.id,
            "flashes": get_flashed_messages(with_categories=True),
        }

    if request.method == "PUT":
        user_id = request.args.get("user_id")
        if User.query.get(user_id) is None:
            flash("Brak użytkownika o tym ID.", "danger")
            return {
                "book_id": book.id,
                "flashes": get_flashed_messages(with_categories=True)(
                    with_categories=True
                ),
            }
        borrow = Borrow(
            user_id=user_id,
            book_id=book.id,
            predicted_return_date=datetime.datetime.now()
            + datetime.timedelta(days=current_app.config["DEFAULT_BORROWING_DAYS"]),
        )
        db.session.add(borrow)
        db.session.commit()
        flash("Pomyślnie wypożyczono książkę.", "success")
        return {
            "book_id": book.id,
            "flashes": get_flashed_messages(with_categories=True),
        }

    return {
        "book": dict_book(book, None),
        "users": users,
        "flashes": get_flashed_messages(with_categories=True),
    }


@api.route("/return-book/<int:borrow_id>", methods=(["PATCH"]))
@moderator_required_api
def return_book(borrow_id):
    borrow = Borrow.query.get_or_404(borrow_id)
    if borrow.return_date:
        flash("Ta książka została już zwrócona.", "danger")
        return {
            "user_id": borrow.user_id,
            "flashes": get_flashed_messages(with_categories=True),
        }
    borrow.return_date = datetime.datetime.now()
    db.session.commit()
    flash("Zwrot książki przebiegł pomyślnie.", "success")
    return {
        "user_id": borrow.user_id,
        "flashes": get_flashed_messages(with_categories=True),
    }


@api.route("/prolong-borrow/<int:borrow_id>", methods=(["PATCH"]))
def prolong_borrow(borrow_id):
    borrow = Borrow.query.get_or_404(borrow_id)
    if not current_user.can(Permission.MODERATOR):
        if borrow.user_id != current_user.id:
            abort(403)

    max_prolong = current_app.config["MAX_PROLONG_TIMES"]

    if borrow.return_date:
        flash("Ta książka została już zwrócona.", "danger")
    elif borrow.prolong_times >= max_prolong:
        flash(f"Wykorzystano maksymalną liczbę przedłużeń ({max_prolong}).", "danger")
    else:
        borrow.predicted_return_date += datetime.timedelta(
            days=current_app.config["PROLONG_DAYS"]
        )
        borrow.prolong_times += 1
        db.session.commit()
        flash(f"Pomyślnie przedłużono wypożyczenie.", "success")

    return {
        "user_id": borrow.user_id,
        "flashes": get_flashed_messages(with_categories=True),
    }


def delete_object(object_id, model):
    obj = model.query.get_or_404(object_id)
    db.session.delete(obj)
    db.session.commit()


@api.route("/delete-user/<int:user_id>", methods=(["DELETE"]))
@admin_required_api
def delete_user(user_id):
    delete_object(user_id, User)
    flash("Pomyślnie usunięto użytkownika.", "success")
    return {
        "flashes": get_flashed_messages(with_categories=True),
    }


@api.route("/delete-book/<int:book_id>", methods=(["DELETE"]))
@admin_required_api
def delete_book(book_id):
    delete_object(book_id, Book)
    flash("Poprawnie usunięto książkę.", "success")
    return {
        "flashes": get_flashed_messages(with_categories=True),
    }


@api.route("/delete-borrow/<int:borrow_id>", methods=(["DELETE"]))
@admin_required_api
def delete_borrow(borrow_id):
    delete_object(borrow_id, Borrow)
    flash("Poprawnie usunięto wypożyczenie.", "success")
    return {
        "flashes": get_flashed_messages(with_categories=True),
    }


# LISTING


@api.route("/list-users", methods=("GET", "POST"))
@moderator_required_api
def list_users():
    phrase = request.args.get("phrase", "")

    if phrase:
        if " " in phrase:
            # name and surname
            phrase = phrase.title()
            splitted_phrase = phrase.split()
            users = (
                User.query.join(PersonalData)
                .filter(
                    PersonalData.name.in_(splitted_phrase),
                    PersonalData.surname.in_(splitted_phrase),
                )
                .order_by(PersonalData.surname)
            )
        else:
            # id, only name, only surname
            try:
                int(phrase)
                users = (
                    User.query.join(PersonalData)
                    .filter_by(id=phrase)
                    .order_by(PersonalData.surname)
                )
            except:
                users = (
                    User.query.join(PersonalData)
                    .filter(
                        or_(
                            PersonalData.name.ilike(f"%{phrase}%"),
                            PersonalData.surname.ilike(f"%{phrase}%"),
                        )
                    )
                    .order_by(PersonalData.surname)
                )
    else:
        users = User.query.join(PersonalData).order_by(PersonalData.surname)

    return {
        "users": [dict_user(user) for user in users],
        "flashes": get_flashed_messages(with_categories=True),
    }


@api.route("/list-borrows-books/", methods=(["GET"]))
@moderator_required_api
def list_borrows_books():
    user_id = request.args.get("user_id", None, type=int)
    if user_id is None:
        abort(404)

    user = User.query.get_or_404(user_id)

    borrowed_books = Borrow.query.filter_by(user_id=user.id).order_by(
        Borrow.return_date.desc().nullsfirst()
    )

    return {
        "borrowed_books": [
            {
                "id": borrow.id,
                "book": dict_book(borrow.book, None),
                "predicted_return_date": borrow.predicted_return_date,
                "return_date": borrow.return_date,
                "prolong_times": borrow.prolong_times,
            }
            for borrow in borrowed_books
        ],
        "max_prolongs": current_app.config["MAX_PROLONG_TIMES"],
    }


@api.route("/list-borrows-users")
@moderator_required_api
def list_borrows_users():
    book_id = request.args.get("book_id", None, int)
    if book_id is None:
        abort(404)

    book = Book.query.get_or_404(book_id)
    borrows = Borrow.query.filter_by(book_id=book.id).order_by(
        Borrow.return_date.desc().nullsfirst()
    )

    return {
        "borrows": [
            {
                "id": borrow.id,
                "user": dict_user(borrow.user),
                "predicted_return_date": borrow.predicted_return_date,
                "return_date": borrow.return_date,
                "prolong_times": borrow.prolong_times,
            }
            for borrow in borrows
        ],
        "max_prolongs": current_app.config["MAX_PROLONG_TIMES"],
    }


@api.route("/all-borrows", methods=("GET", "POST"))
@moderator_required_api
def all_borrows():
    borrows = Borrow.query.order_by(Borrow.return_date.desc().nullsfirst())

    return {
        "borrows": [
            {
                "id": borrow.id,
                "user": dict_user(borrow.user),
                "book": dict_book(borrow.book, None),
                "predicted_return_date": borrow.predicted_return_date,
                "return_date": borrow.return_date,
                "prolong_times": borrow.prolong_times,
            }
            for borrow in borrows
        ],
        "max_prolongs": current_app.config["MAX_PROLONG_TIMES"],
    }
