from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import current_app
from flask import abort

import datetime
from isbnlib import clean
from isbnlib import desc
from isbnlib import meta
from isbnlib import is_isbn10
from isbnlib import is_isbn13
from sqlalchemy import or_

from .forms import BookForm
from .forms import SearchUserForm
from .forms import BorrowBookForm
from . import moderate
from .. import db

from ..models import Book, PersonalData
from ..models import User
from ..models import Author
from ..models import Borrow
from ..auth.decorators import moderator_required


@moderate.route("/add-book", methods=("GET", "POST"))
@moderator_required
def add_book():
    form = BookForm(request.form)
    if form.validate_on_submit():
        category = form.add_category.data if form.add_category.data else form.category.data
        publisher = form.add_publisher.data if form.add_publisher.data else form.publisher.data

        author_id = form.author.data
        if form.add_author.data:
            new_author = Author(full_name=form.add_author.data)
            db.session.add(new_author)
            db.session.commit()
            author_id = new_author.id

        new_book = Book(
            isbn=clean(form.isbn.data),
            title=form.title.data,
            category=category,
            description=form.description.data,
            author_id=author_id,
            number_of_copies=form.number_of_copies.data,
            cover=request.files["cover"].stream.read() if request.files.get("cover") else None,
            publisher=publisher,
            pages=form.pages.data,
            year=form.year.data
        )

        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for("main.book_details", id=new_book.id))
    elif form.isbn.data:
        isbn = clean(form.isbn.data)
        if is_isbn13(isbn) or is_isbn10(isbn):
            book_info = meta(isbn)
            if book_info:
                if book_info.get("Title") and not form.title.data:
                    form.title.data = book_info["Title"]
                    form.title.errors = []
                if book_info.get("Year") and not form.year.data:
                    form.year.data = book_info["Year"]
                    form.year.errors = []
                if not form.description.data:
                    form.description.data = desc(isbn)


    form.category.choices = [category[0] for category in db.session.query(Book.category).distinct().all()]
    form.author.choices = [(author.id, author.full_name) for author in Author.query.all()]
    form.publisher.choices = [publisher[0] for publisher in db.session.query(Book.publisher).distinct().all()]

    return render_template(
        "moderate/book_form.html",
        title="Dodaj książkę",
        dont_show_search_bar=True,
        form=form,
        heading="Dodaj książkę do księgozbioru"
    )

@moderate.route("/edit-book/<int:id>", methods=("GET", "POST"))
@moderator_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    form = BookForm(request.form, obj=book)

    if form.validate_on_submit():
        book.isbn = form.isbn.data
        book.title = form.title.data
        book.category = form.category.data
        book.description = form.description.data
        book.author_id = form.author.data
        book.number_of_copies = form.number_of_copies.data
        book.publisher = form.publisher.data
        book.pages = form.pages.data
        book.year = form.year.data
        cover = request.files["cover"].stream.read() if request.files.get("cover") else ""
        if len(cover) > 0:
            book.cover = cover
        db.session.commit()

        flash("Edycja książki przebiegła pomyślnie.", category="success")
        return redirect(url_for("main.book_details", id=book.id))

    form.category.choices = [category[0] for category in db.session.query(Book.category).distinct().all()]
    form.author.choices = [(author.id, author.full_name) for author in Author.query.all()]
    form.publisher.choices = [publisher[0] for publisher in db.session.query(Book.publisher).distinct().all()]

    form.category.data = book.category
    form.author.data = book.author_id
    form.publisher.data = book.publisher

    return render_template(
        "moderate/book_form.html",
        title="Edytuj książkę",
        dont_show_search_bar=True,
        form=form,
        heading="Edytuj książkę z księgozbioru",
        button_value="Edytuj książkę"
    )

@moderate.route("/borrow-book/<int:id>", methods=("GET", "POST"))
@moderator_required
def borrow_book(id):
    form = BorrowBookForm()
    form.users.choices = [(user.id, f"{user.personal_data[0].name} {user.personal_data[0].surname} ({ user.id })") for user in User.query.all()]
    book = Book.query.get_or_404(id)
    borrows = [borrow for borrow in book.borrows if borrow.return_date is None]
    if len(borrows) >= book.number_of_copies:
        flash("Brak dostępnych kopii do wypożyczenia.", category="danger")
        return redirect(url_for("main.book_details", id=book.id))

    if form.validate_on_submit():
        user_id = form.users.data
        if form.user_id.data:
            user_id = form.user_id.data
        borrow = Borrow(
            user_id=user_id,
            book_id=book.id,
        )
        db.session.add(borrow)
        db.session.commit()
        flash("Pomyślnie wypożyczono książkę.", category="success")
        return redirect(url_for("main.book_details", id=book.id))

    return render_template(
        "moderate/borrow_book.html",
        title="Wypożycz książkę",
        dont_show_search_bar=True,
        form=form,
        heading="Wypożycz książkę z księgozbioru",
        button_value="Wypożycz książkę",
        book=book
    )

@moderate.route("/list-users", methods=("GET", "POST"))
@moderator_required
def list_users():
    form = SearchUserForm(request.form)

    page = request.args.get("page", 1, type=int)
    phrase = form.phrase.data = request.args.get("phrase", "")

    if phrase:
        if " " in phrase:
            # name and surname
            phrase = phrase.title()
            splitted_phrase = phrase.split()
            users_paginate = User.query \
                .join(PersonalData) \
                .filter(
                    PersonalData.name.in_(splitted_phrase),
                    PersonalData.surname.in_(splitted_phrase)
                ) \
                .order_by(PersonalData.surname) \
                .paginate(page, current_app.config["USERS_PER_PAGE"])
        else:
            # id, only name, only surname
            try:
                int(phrase)
                users_paginate = User.query \
                    .join(PersonalData) \
                    .filter_by(id=phrase) \
                    .order_by(PersonalData.surname) \
                    .paginate(page, current_app.config["USERS_PER_PAGE"])
            except:
                users_paginate = User.query \
                    .join(PersonalData) \
                    .filter(
                        or_(
                            PersonalData.name.ilike(f"%{phrase}%"),
                            PersonalData.surname.ilike(f"%{phrase}%")
                        )
                    ) \
                    .order_by(PersonalData.surname) \
                    .paginate(page, current_app.config["USERS_PER_PAGE"])
    else:
        users_paginate = User.query \
                .join(PersonalData) \
                .order_by(PersonalData.surname) \
                .paginate(page, current_app.config["USERS_PER_PAGE"])
    return render_template(
        "moderate/list_users.html",
        title="Lista użytkowników",
        dont_show_search_bar=True,
        heading="Lista wszystkich użytkowników",
        users=users_paginate.items,
        page=page,
        pagination=users_paginate,
        form=form
    )

@moderate.route("/list-borrows-books/", methods=("GET", "POST"))
@moderator_required
def list_borrows_books():
    user_id = request.args.get("user_id", None, type=int)
    if user_id is None:
        abort(404)
    user = User.query.get_or_404(user_id)
    page = request.args.get("page", 1, type=int)

    borrowed_books = Borrow.query. \
        filter_by(user_id=user_id). \
        order_by(Borrow.return_date.desc().nullsfirst()). \
        paginate(page, current_app.config["BOOKS_PER_PAGE"])

    return render_template(
        "moderate/list_borrows_books.html",
        title="Wypożyczenia",
        dont_show_search_bar=True,
        heading=f"Wypożyczenia użytkownika {user.personal_data[0].name} {user.personal_data[0].surname}",
        borrowed_books=borrowed_books.items,
        page=page,
        pagination=borrowed_books
    )

@moderate.route("/return-book/<int:borrow_id>", methods=("GET", "POST"))
@moderator_required
def return_book(borrow_id):
    borrow = Borrow.query.get_or_404(borrow_id)
    if borrow.return_date:
        flash("Ta książka została już zwrócona.", category="danger")
        return redirect(url_for("moderate.list_borrows_books", user_id=borrow.user_id))
    borrow.return_date = datetime.datetime.now()
    db.session.commit()
    flash("Zwrot książki przebiegł pomyślnie.", category="success")
    return redirect(url_for("moderate.list_borrows_books", user_id=borrow.user_id))