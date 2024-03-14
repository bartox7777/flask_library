from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import current_app
from flask import abort

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

from . import api
from .. import mail
from .. import db

from ..models import Book
from ..models import PersonalData
from ..models import User
from ..models import Author
from ..models import Borrow
from ..models import Role
from ..models import Permission

from .decorators import moderator_required_api
from .decorators import admin_required_api


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
