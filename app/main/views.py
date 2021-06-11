from flask import render_template

import io
from PIL import Image

from . import main
from .forms import SearchForm
from ..models import Book


@main.route("/", methods=("GET", "POST"))
def index():
    form = SearchForm()
    newest_books = Book.query.order_by(Book.add_date.desc()).limit(5).all()
    processed_covers = []

    # cover processing
    for book in newest_books:
        cover = Image.open(io.BytesIO(book.cover))
        # print(book.cover)
    return render_template("main/index.html", title="Strona główna", form=form)

@main.route("/search", methods=("GET", "POST"))
def search():
    return render_template("main/search.html", title="Panel wyszukiwania")
