from flask import request
from flask import current_app
from flask import render_template

import io
from PIL import Image
from base64 import b64encode
from sqlalchemy import or_

from . import main
from .forms import SearchForm
from ..models import Book
from ..models import Author
from ..models import Borrow


def process_covers(books, width=200, height=300, class_="img-thumbnail p-1 m-2"):
    processed_covers = []
        # cover processing
    for book in books:
        # cover_file_like = io.BytesIO(book.cover)

        # doing this to get image format
        try:
            cover = Image.open(io.BytesIO(book.cover))
            cover_file_like = io.BytesIO()
            cover.save(cover_file_like, cover.format)
            cover_file_like.seek(0)
            img_tag = f'''
                <img
                    class={class_}
                    style="width: {width}px; height: {height}px"
                    src="data:image/{cover.format.lower()};base64,{b64encode(cover_file_like.read()).decode()}">
            '''
        except:
            img_tag = f'''
                <img
                    class={class_}
                    style="width: {width}px; height: {height}px"
                    src="">
            '''
        processed_covers.append(img_tag)

    return list(zip(books, processed_covers))

@main.route("/", methods=("GET", "POST"))
def index():
    newest_books = Book.query.order_by(Book.add_date.desc()).limit(5).all()

    return render_template(
        "main/index.html",
        title="Strona główna",
        form=SearchForm(),
        newest_books=process_covers(newest_books)
    )


@main.route("/search/", methods=("GET", "POST"))
def search():
    form = SearchForm(request.form)

    page = request.args.get("page", 1, type=int)
    search_by = form.search_by.data = request.args.get("search_by", "phrase")
    phrase = form.phrase.data = request.args.get("phrase", "")

    # TODO: it is better to use some search engine
    if search_by == "phrase":
        found_books = Book.query \
            .join(Author, Author.id==Book.author_id) \
            .filter(
            or_(
                Book.title.ilike(f"%{phrase}%"),
                Book.description.ilike(f"%{phrase}%"),
                Book.publisher.ilike(f"%{phrase}%"),
                Author.full_name.ilike(f"%{phrase}%")
            )
        ).paginate(page, current_app.config["BOOKS_PER_PAGE"])
    elif search_by == "title":
        found_books = Book.query \
            .filter(
                Book.title.ilike(f"%{phrase}%"),
            ).paginate(page, current_app.config["BOOKS_PER_PAGE"])
    elif search_by == "category":
        found_books = Book.query \
            .filter(
                Book.category.ilike(f"%{phrase}%"),
            ).paginate(page, current_app.config["BOOKS_PER_PAGE"])
    elif search_by == "author":
            found_books = Book.query \
            .join(Author, Author.id==Book.author_id) \
            .filter(
            Author.full_name.ilike(f"%{phrase}%")
        ).paginate(page, current_app.config["BOOKS_PER_PAGE"])
    elif search_by == "publisher":
            found_books = Book.query \
            .filter(
                Book.publisher.ilike(f"%{phrase}%"),
            ).paginate(page, current_app.config["BOOKS_PER_PAGE"])
    else:
        found_books = Book.query.paginate(page, current_app.config["BOOKS_PER_PAGE"])
    return render_template(
        "main/search.html",
        title="Panel wyszukiwania",
        form=form,
        found_books=process_covers(found_books.items),
        pagination=found_books,
        page=page,
        advanced_search=True
    )

@main.route("/book-details/<int:id>", methods=("GET", "POST"))
def book_details(id):
    book = Book.query.get_or_404(id)
    cover = process_covers([book])[0][1]
    borrows = [borrow for borrow in book.borrows if borrow.return_date is None]
    available_copies = book.number_of_copies - len(borrows)

    return render_template(
        "main/book_details.html",
        title="Szczegóły ksiązki",
        book=book,
        form=SearchForm(),
        cover=cover,
        available_copies=available_copies
    )