from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import current_app
from flask import abort

import random
import string
import datetime
from isbnlib import clean
from isbnlib import desc
from isbnlib import meta
from isbnlib import is_isbn10
from isbnlib import is_isbn13
from sqlalchemy import or_

from .forms import BookForm
from .forms import UserForm
from .forms import SearchUserForm
from .forms import BorrowBookForm
from . import moderate
from .. import db

from ..models import Book, PersonalData
from ..models import User
from ..models import Author
from ..models import Borrow
from ..models import Role
from ..auth.decorators import moderator_required
from ..auth.decorators import admin_required


@moderate.route("/add-book", methods=("GET", "POST"))
@moderator_required
def add_book():
    form = BookForm(request.form)
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
            cover=request.files["cover"].stream.read() if request.files.get("cover") else None,
            publisher=publisher,
            pages=form.pages.data,
            year=form.year.data
        )

        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for("main.book_details", book_id=new_book.id))
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
        "moderate/book_form.html",
        title="Dodaj książkę",
        dont_show_search_bar=True,
        form=form,
        heading="Dodaj książkę do księgozbioru",
        button_value="Dodaj książkę"
    )

@moderate.route("/edit-book/<int:book_id>", methods=("GET", "POST"))
@moderator_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(request.form, obj=book)

    if form.validate_on_submit():
        book.isbn = form.isbn.data
        book.title = form.title.data
        book.category = form.category.data
        book.description = form.description.data
        book.author_id = form.author.data
        book.number_of_copies = form.number_of_copies.data
        book.publisher = form.publisher.data
        book.pages = form.pages.data
        book.year = form.year.data
        cover = request.files["cover"].stream.read() if request.files.get("cover") else ""
        if len(cover) > 0:
            book.cover = cover
        db.session.commit()

        flash("Edycja książki przebiegła pomyślnie.", "success")
        return redirect(url_for("main.book_details", book_id=book.id))

    form.category.choices = [category[0] for category in db.session.query(Book.category).distinct().all()]
    form.author.choices = [(author.id, author.full_name) for author in Author.query.all()]
    form.publisher.choices = [publisher[0] for publisher in db.session.query(Book.publisher).distinct().all()]

    form.category.data = book.category
    form.author.data = book.author_id
    form.publisher.data = book.publisher

    return render_template(
        "moderate/book_form.html",
        title="Edytuj książkę",
        dont_show_search_bar=True,
        form=form,
        heading="Edytuj książkę z księgozbioru",
        button_value="Edytuj książkę",
        editing=True,
        book=book
    )

@moderate.route("/borrow-book/<int:book_id>", methods=("GET", "POST"))
@moderator_required
def borrow_book(book_id):
    form = BorrowBookForm()
    form.users.choices = [(user.id, f"{user.full_name} ({ user.id })") for user in User.query.all()]
    book = Book.query.get_or_404(book_id)
    borrows = [borrow for borrow in book.borrows if borrow.return_date is None]
    if len(borrows) >= book.number_of_copies:
        flash("Brak dostępnych kopii do wypożyczenia.", "danger")
        return redirect(url_for("main.book_details", book_id=book.id))

    if form.validate_on_submit():
        user_id = form.users.data
        if form.user_id.data:
            user_id = form.user_id.data
        if User.query.get(user_id) is None:
            flash("Brak użytkownika o tym ID.", "danger")
            return redirect(url_for("moderate.borrow_book", book_id=book.id))
        borrow = Borrow(
            user_id=user_id,
            book_id=book.id,
            predicted_return_date=datetime.datetime.now() + datetime.timedelta(days=current_app.config["DEFAULT_BORROWING_DAYS"])
        )
        db.session.add(borrow)
        db.session.commit()
        flash("Pomyślnie wypożyczono książkę.", "success")
        return redirect(url_for("main.book_details", book_id=book.id))

    return render_template(
        "moderate/borrow_book.html",
        title="Wypożycz książkę",
        dont_show_search_bar=True,
        form=form,
        heading="Wypożycz książkę z księgozbioru",
        button_value="Wypożycz książkę",
        book=book
    )

@moderate.route("/list-users", methods=("GET", "POST"))
@moderator_required
def list_users():
    form = SearchUserForm(request.form)

    page = request.args.get("page", 1, type=int)
    phrase = form.phrase.data = request.args.get("phrase", "")

    if phrase:
        if " " in phrase:
            # name and surname
            phrase = phrase.title()
            splitted_phrase = phrase.split()
            users_paginate = User.query \
                .join(PersonalData) \
                .filter(
                    PersonalData.name.in_(splitted_phrase),
                    PersonalData.surname.in_(splitted_phrase)
                ) \
                .order_by(PersonalData.surname) \
                .paginate(page, current_app.config["USERS_PER_PAGE"])
        else:
            # id, only name, only surname
            try:
                int(phrase)
                users_paginate = User.query \
                    .join(PersonalData) \
                    .filter_by(id=phrase) \
                    .order_by(PersonalData.surname) \
                    .paginate(page, current_app.config["USERS_PER_PAGE"])
            except:
                users_paginate = User.query \
                    .join(PersonalData) \
                    .filter(
                        or_(
                            PersonalData.name.ilike(f"%{phrase}%"),
                            PersonalData.surname.ilike(f"%{phrase}%")
                        )
                    ) \
                    .order_by(PersonalData.surname) \
                    .paginate(page, current_app.config["USERS_PER_PAGE"])
    else:
        users_paginate = User.query \
                .join(PersonalData) \
                .order_by(PersonalData.surname) \
                .paginate(page, current_app.config["USERS_PER_PAGE"])
    return render_template(
        "moderate/list_users.html",
        title="Lista użytkowników",
        dont_show_search_bar=True,
        heading="Lista wszystkich użytkowników",
        users=users_paginate.items,
        page=page,
        pagination=users_paginate,
        form=form
    )

@moderate.route("/list-borrows-books/", methods=("GET", "POST"))
@moderator_required
def list_borrows_books():
    user_id = request.args.get("user_id", None, type=int)
    if user_id is None:
        abort(404)
    user = User.query.get_or_404(user_id)
    page = request.args.get("page", 1, type=int)

    borrowed_books = Borrow.query. \
        filter_by(user_id=user_id). \
        order_by(Borrow.return_date.desc().nullsfirst()). \
        paginate(page, current_app.config["BOOKS_PER_PAGE"])

    return render_template(
        "moderate/list_borrows_books.html",
        title="Wypożyczenia",
        dont_show_search_bar=True,
        heading=f"Wypożyczenia użytkownika {user.full_name}",
        borrowed_books=borrowed_books.items,
        page=page,
        pagination=borrowed_books,
        datetime_now=datetime.datetime.now(),
        max_prolongs=current_app.config["MAX_PROLONG_TIMES"]
    )

@moderate.route("/return-book/<int:borrow_id>", methods=("GET",))
@moderator_required
def return_book(borrow_id):
    borrow = Borrow.query.get_or_404(borrow_id)
    if borrow.return_date:
        flash("Ta książka została już zwrócona.", "danger")
        return redirect(request.referrer or url_for("moderate.list_borrows_books", user_id=borrow.user_id))
    borrow.return_date = datetime.datetime.now()
    db.session.commit()
    flash("Zwrot książki przebiegł pomyślnie.", "success")
    return redirect(request.referrer or url_for("moderate.list_borrows_books", user_id=borrow.user_id))

@moderate.route("/edit-user/<int:user_id>", methods=("GET", "POST"))
@moderator_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    form = UserForm(request.form, obj=user.personal_data[0])
    form.role.choices = [(role.id, role.name) for role in Role.query.filter_by()]

    if form.validate_on_submit():
        user.personal_data[0].name = form.name.data
        user.personal_data[0].surname = form.surname.data
        user.personal_data[0].phone_number = form.phone_number.data
        user.personal_data[0].extended_city = form.extended_city.data
        user.personal_data[0].extended_street = form.extended_street.data
        user.email = form.email.data
        user.role_id = form.role.data
        user.activated = form.activated.data
        db.session.commit()
        flash("Pomyślnie zedytowano dane.", "success")
        return redirect(url_for("moderate.edit_user", user_id=user.id))

    form.email.data = user.email
    form.activated.data = user.activated
    form.role.data = str(user.role_id)

    return render_template(
        "moderate/user_form.html",
        title="Edytuj użytkownika",
        form=form,
        dont_show_search_bar=True,
        heading="Edytuj dane użytkownika",
        button_value="Edytuj użytkownika",
        user=user
    )

@moderate.route("/add-user", methods=("GET", "POST"))
@moderator_required
def add_user():
    form = UserForm(request.form)
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]
    if form.validate_on_submit():
        error = False
        if User.query.filter_by(email=form.email.data).first():
            form.email.errors.append("Ten email jest już przypisany.")
            error = True
        if PersonalData.query.filter_by(phone_number=form.phone_number.data).first():
            form.phone_number.errors.append("Ten numer telefonu jest już przypisany.")
            error = True

        if not error:
            password = "".join(random.choices(string.ascii_letters+string.digits, k=8))

            new_user = User(
                email=form.email.data,
                role_id=form.role.data,
                password=password,
            )
            db.session.add(new_user)
            db.session.commit()

            new_user_personal_data = PersonalData(
                name=form.name.data,
                surname=form.surname.data,
                phone_number=form.phone_number.data,
                extended_city=form.extended_city.data,
                extended_street=form.extended_street.data,
                user_id=new_user.id
            )
            db.session.add(new_user_personal_data)
            db.session.commit()

            print(f"EMAIL TO: {new_user.email}\nPASSWORD: {password}")
            flash(f"Użytkownik { new_user.full_name } dodany pomyślnie.", "success")
            flash(f"Hasło zostało wysłane na podanego e-maila.", "info")
            return redirect(url_for("moderate.edit_user", user_id=new_user.id))

    role_user_id = Role.query.filter_by(name="user").first().id
    form.role.data = str(role_user_id)
    form.activated.render_kw = {"disabled": True}

    return render_template(
        "moderate/user_form.html",
        title="Dodaj użytkownika",
        form=form,
        dont_show_search_bar=True,
        heading="Dodaj nowego użytkownika",
        button_value="Dodaj użytkownika"
    )

@moderate.route("/prolong_borrow/<int:borrow_id>", methods=("GET",))
@moderator_required
def prolong_borrow(borrow_id):
    borrow = Borrow.query.get_or_404(borrow_id)
    max_prolong = current_app.config["MAX_PROLONG_TIMES"]
    if borrow.prolong_times >= max_prolong:
        flash(f"Wykorzystano maksymalną liczbę przedłużeń ({max_prolong}).", "danger")
    else:
        borrow.predicted_return_date += datetime.timedelta(days=current_app.config["PROLONG_DAYS"])
        borrow.prolong_times += 1
        db.session.commit()
        flash(f"Pomyślnie przedłużono wypożyczenie.", "success")

    return redirect(request.referrer or url_for("moderate.list_borrows_books", user_id=borrow.user_id))

@moderate.route("/list-borrows-users")
@moderator_required
def list_borrows_users():
    book_id = request.args.get("book_id", None, int)
    if book_id is None:
        abort(404)
    page = request.args.get("page", 1, int)

    book = Book.query.get_or_404(book_id)
    borrows = Borrow.query. \
        filter_by(book_id=book.id). \
        order_by(Borrow.return_date.desc().nullsfirst()). \
        paginate(page, current_app.config["USERS_PER_PAGE"])

    return render_template(
        "moderate/list_borrows_users.html",
        title="Wypożyczenia",
        heading=f"Wypożyczenia książki \"{book.title}\"",
        dont_show_search_bar=True,
        borrows=borrows.items,
        pagination=borrows,
        datetime_now=datetime.datetime.now(),
        max_prolongs=current_app.config["MAX_PROLONG_TIMES"]
    )

@moderate.route("/all-borrows", methods=("GET", "POST"))
@moderator_required
def all_borrows():
    page = request.args.get("page", 1, int)

    borrows = Borrow.query. \
    order_by(Borrow.return_date.desc().nullsfirst()). \
    paginate(page, current_app.config["USERS_PER_PAGE"])

    return render_template(
        "moderate/all_borrows.html",
        title="Wszystkie wypożyczenia",
        heading="Wszystkie wypożyczenia książek",
        borrows=borrows.items,
        pagination=borrows,
        dont_show_search_bar=True,
        datetime_now=datetime.datetime.now(),
        max_prolongs=current_app.config["MAX_PROLONG_TIMES"]
    )

@moderate.route("/delete-user/<int:user_id>", methods=("GET",))
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Pomyślnie usunięto użytkownika.", "success")
    return redirect(url_for("moderate.list_users"))

@moderate.route("/delete-book/<int:book_id>", methods=("GET",))
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash("Poprawnie usunięto książkę.", "success")
    return redirect(url_for("main.search"))

@moderate.route("/delete-borrow/<int:borrow_id>", methods=("GET",))
@admin_required
def delete_borrow(borrow_id):
    borrow = Borrow.query.get_or_404(borrow_id)
    db.session.delete(borrow)
    db.session.commit()
    flash("Poprawnie usunięto wypożyczenie.", "success")
    return redirect(request.referrer or url_for("moderate.all_borrows"))