from flask import render_template

from . import main
from .forms import SearchForm


@main.route("/", methods=("GET", "POST"))
def index():
    form = SearchForm()
    return render_template("main/index.html", title="Strona główna", form=form)

@main.route("/search", methods=("GET", "POST"))
def search():
    return render_template("main/search.html", title="Panel wyszukiwania")