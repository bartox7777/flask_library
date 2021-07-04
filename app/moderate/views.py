from flask import render_template
from flask import request

from .forms import AddBookForm
from . import moderate
from .. import db
from ..models import Book
from ..models import Author


@moderate.route("/add-book", methods=("GET", "POST"))
def add_book():
    form = AddBookForm(request.form)
    if form.validate_on_submit():
        # print(request.files)
        pass

    form.category.choices = [category[0] for category in db.session.query(Book.category).distinct().all()]
    form.author.choices = [(author.id, author.full_name) for author in Author.query.all()]
    form.publisher.choices = [publisher[0] for publisher in db.session.query(Book.publisher).distinct().all()]

    return render_template(
        "moderate/add_book.html",
        title="Dodaj książkę",
        dont_show_search_bar=True,
        form=form
    )