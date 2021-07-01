from flask import render_template
from ..main.forms import SearchForm

from . import moderate


@moderate.route("/add-book", methods=("GET", "POST"))
def add_book():
    return render_template(
        "moderate/add_book.html",
        title="Dodaj książkę",
        dont_show_search_bar=True
    )