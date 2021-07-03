from flask import render_template
from .forms import AddBookForm

from . import moderate
from .. import db
from ..models import Book


@moderate.route("/add-book", methods=("GET", "POST"))
def add_book():
    form = AddBookForm()
    form.category.choices = [(category[0], category[0]) for category in db.session.query(Book.category).distinct().all()]

    return render_template(
        "moderate/add_book.html",
        title="Dodaj książkę",
        dont_show_search_bar=True,
        form=form
    )