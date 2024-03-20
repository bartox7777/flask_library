from flask import flash
from flask import jsonify
from flask import request
from flask import current_app
from flask import get_flashed_messages

import io
from PIL import Image
from base64 import b64encode
from sqlalchemy import or_
from flask_login import current_user

from . import api
from ..models import Borrow
from ..models import Book
from ..models import Author
from ..models import Borrow
from app.api.decorators import login_required_api


# @api.before_request
# def check_if_activated():
#     if current_user.is_authenticated and not current_user.activated:
#         print(current_user.is_authenticated)
#         print(current_user.activated)
#         flash("Aktywuj swoje konto przez zmianę hasła.", "warning")
#         return jsonify({"flashes": get_flashed_messages()}), 403


def process_covers(books):
    processed_covers = []
    for book in books:
        cover = Image.open(io.BytesIO(book.cover))
        cover_file_like = io.BytesIO()
        cover.save(cover_file_like, cover.format)
        cover_file_like.seek(0)
        processed_covers.append(
            f"data:image/{cover.format.lower()};base64,{b64encode(cover_file_like.read()).decode()}"
        )

    return list(zip(books, processed_covers))


def dict_book(book, cover):
    return {
        "book_id": book.id,
        "isbn": book.isbn,
        "title": book.title,
        "category": book.category,
        "description": book.description,
        "author_id": book.author_id,
        "add_date": book.add_date,
        "number_of_copies": book.number_of_copies,
        "cover": cover,
        "publisher": book.publisher,
        "pages": book.pages,
        "year": book.year,
    }


def dict_borrow(borrow):
    return {
        "borrow_id": borrow.id,
        "user_id": borrow.user_id,
        "book_id": borrow.book_id,
        "data": borrow.date,
        "prolong_times": borrow.prolong_times,
        "predicted_return_date": borrow.predicted_return_date,
        "return_date": borrow.return_date,
    }


@api.route("/", methods=(["GET"]))
def index():
    newest_books = Book.query.order_by(Book.add_date.desc()).limit(5).all()
    return jsonify(
        [dict_book(book, cover) for book, cover in process_covers(newest_books)]
    )


@api.route("/search/", methods=(["GET"]))
def search():
    search_by = request.args.get("search_by", "phrase")
    phrase = request.args.get("phrase", "")

    if search_by == "phrase":
        found_books = Book.query.join(Author, Author.id == Book.author_id).filter(
            or_(
                Book.title.ilike(f"%{phrase}%"),
                Book.description.ilike(f"%{phrase}%"),
                Book.publisher.ilike(f"%{phrase}%"),
                Author.full_name.ilike(f"%{phrase}%"),
            )
        )
    elif search_by == "title":
        found_books = Book.query.filter(
            Book.title.ilike(f"%{phrase}%"),
        )
    elif search_by == "category":
        found_books = Book.query.filter(
            Book.category.ilike(f"%{phrase}%"),
        )
    elif search_by == "author":
        found_books = Book.query.join(Author, Author.id == Book.author_id).filter(
            Author.full_name.ilike(f"%{phrase}%")
        )
    elif search_by == "publisher":
        found_books = Book.query.filter(
            Book.publisher.ilike(f"%{phrase}%"),
        )
    else:
        found_books = Book.query.all()

    return jsonify(
        [dict_book(book, cover) for book, cover in process_covers(found_books)]
    )


@api.route("/book-details/<int:book_id>", methods=(["GET"]))
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    cover = process_covers([book])[0][1]
    borrows = [borrow for borrow in book.borrows if borrow.return_date is None]
    available_copies = book.number_of_copies - len(borrows)

    return {"borrows": borrows, "available_copies": available_copies, "cover": cover}


@api.route("/borrowed-books", methods=(["GET"]))
@login_required_api
def borrowed_books():
    borrows = Borrow.query.filter_by(user_id=current_user.id).order_by(
        Borrow.return_date.desc().nullsfirst()
    )

    return {
        "borrowed_books": [dict_borrow(borrow) for borrow in borrows],
        "max_prolongs": current_app.config["MAX_PROLONG_TIMES"],
    }
