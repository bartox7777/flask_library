from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

from isbnlib import clean
from isbnlib import desc
from isbnlib import meta
from isbnlib import is_isbn10
from isbnlib import is_isbn13

from .forms import AddBookForm
from . import moderate
from .. import db

from ..models import Book
from ..models import Author
from ..auth.decorators import moderator_required


@moderate.route("/add-book", methods=("GET", "POST"))
@moderator_required
def add_book():
    form = AddBookForm(request.form)
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
            cover=request.files["cover"].stream.read(),
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
        "moderate/add_book.html",
        title="Dodaj książkę",
        dont_show_search_bar=True,
        form=form
    )