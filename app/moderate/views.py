from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

from isbnlib import clean
from isbnlib import desc
from isbnlib import meta
from isbnlib import is_isbn10
from isbnlib import is_isbn13

from .forms import BookForm
from .forms import BorrowBook
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
    form = BorrowBook()
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
    users = User.query \
            .join(PersonalData) \
            .order_by(PersonalData.surname) \
            .all()
    print(users)
    return render_template(
        "moderate/list_users.html",
        title="Lista użytkowników",
        dont_show_search_bar=True,
        heading="Lista wszystkich użytkowników",
        users=users
    )