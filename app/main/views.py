from flask import abort
from flask import url_for
from flask import request
from flask import redirect
from flask import render_template

import io
from PIL import Image
from base64 import b64encode
from sqlalchemy import or_

from . import main
from .forms import SearchForm
from ..models import Book
from ..models import Author


def process_covers(books, width=200, height=300, class_="img-thumbnail p-1 m-2"):
    processed_covers = []
        # cover processing
    for book in books:
        # cover_file_like = io.BytesIO(book.cover)

        # doing this to get image format
        cover = Image.open(io.BytesIO(book.cover))
        cover_file_like = io.BytesIO()
        cover.save(cover_file_like, cover.format)
        cover_file_like.seek(0)
        img_tag = f'<img class={class_} style="width: {width}px; height: {height}px" src="data:image/{cover.format.lower()};base64,{b64encode(cover_file_like.read()).decode()}">'
        processed_covers.append(img_tag)

    return list(zip(books, processed_covers))

@main.route("/", methods=("GET", "POST"))
def index():
    form = SearchForm()
    if form.validate_on_submit():
        phrase = form.phrase.data
        if phrase:
            return redirect(url_for("main.search", phrase=phrase))

    newest_books = Book.query.order_by(Book.add_date.desc()).limit(5).all()


    return render_template("main/index.html", title="Strona główna", form=form, newest_books=process_covers(newest_books))

@main.route("/search", methods=("GET", "POST"))
def search():
    form = SearchForm()
    if form.validate_on_submit():
        phrase = form.phrase.data
    else:
        phrase = request.args.get("phrase", "")
        form.phrase.data = phrase

    # TODO: it is better to use some search engine
    # TODO: need to use pagination
    if phrase:
        found_books = Book.query.join(Author, Author.id==Book.author_id).filter(
            or_(
                Book.title.like(f"%{phrase}%"),
                Book.description.like(f"%{phrase}%"),
                Author.full_name.like(f"%{phrase}%")
            )
        ).all()
    else:
        found_books = Book.query.all()
    return render_template("main/search.html", title="Panel wyszukiwania", form=form, found_books=process_covers(found_books))

@main.route("/book-details/<int:id>", methods=("GET", "POST"))
def book_details(id):
    form = SearchForm()
    if form.validate_on_submit():
        phrase = form.phrase.data
        if phrase:
            return redirect(url_for("main.search", phrase=phrase))

    book = Book.query.get_or_404(id)
    cover = process_covers([book])[0][1]
    return render_template("main/book_details.html", title="Szczegóły ksiązki", book=book, form=form, cover=cover)