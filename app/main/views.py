from flask import render_template

import io
from PIL import Image
from base64 import b64encode

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
        # cover_file_like = io.BytesIO(book.cover)

        # doing this to get image format
        cover = Image.open(io.BytesIO(book.cover))
        cover_file_like = io.BytesIO()
        cover.save(cover_file_like, cover.format)
        cover_file_like.seek(0)
        img_tag = f'<img class="img-thumbnail p-1 m-2" style="width: 200px; height: 300px" src="data:image/{cover.format.lower()};base64,{b64encode(cover_file_like.read()).decode()}">'
        processed_covers.append(img_tag)

    return render_template("main/index.html", title="Strona główna", form=form, newest_books=list(zip(newest_books, processed_covers)))

@main.route("/search", methods=("GET", "POST"))
def search():
    return render_template("main/search.html", title="Panel wyszukiwania")
