from flask import render_template
from .forms import AddBookForm

from . import moderate


@moderate.route("/add-book", methods=("GET", "POST"))
def add_book():
    form = AddBookForm()

    return render_template(
        "moderate/add_book.html",
        title="Dodaj książkę",
        dont_show_search_bar=True,
        form=form
    )