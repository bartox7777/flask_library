from flask import current_app
from flask.cli import with_appcontext

import os
import click
from faker import Faker
from random import randint
from random import choice

from . import db
from .models import *
from flask_migrate import init
from flask_migrate import migrate
from flask_migrate import upgrade


@click.command()
@with_appcontext
def init_db():
    if not current_app.config["TESTING"]:
        init()
        migrate()
        upgrade()
    else:
        db.create_all()

    Role.insert_roles()

    click.echo("Database initialized.")

@click.command()
@click.option("--additional-users", default=10, help="Number of additional users.")
@click.option("--books", default=5, help="Number of books.")
@with_appcontext
def insert_test_data(additional_users, books):
    # USER
    role_user_id = Role.query.filter_by(name="user").first().id
    role_moderator_id = Role.query.filter_by(name="moderator").first().id
    role_admin_id = Role.query.filter_by(name="admin").first().id

    test_admin = User(email="test@test.admin", password="test", activated=True, role_id=role_admin_id)
    test_moderator = User(email="test@test.moderator", password="test", activated=True, role_id=role_moderator_id)
    test_user = User(email="test@test.user", password="test", activated=True, role_id=role_user_id)
    test_user_inactive = User(email="test@test.user-inactive", password="test", activated=False, role_id=role_user_id)

    db.session.add_all([test_admin, test_moderator, test_user, test_user_inactive])

    fake = Faker()

    # PERSONAL DATA
    for _ in range(additional_users):
        user = User(email=fake.unique.ascii_email(), password="test", activated=True, role_id=role_user_id)
        db.session.add(user)
    fake.unique.clear()

    db.session.commit()

    for user in User.query.all():
        user_personal_data = PersonalData(
            name=fake.first_name(),
            surname=fake.last_name(),
            phone_number=fake.phone_number(),
            extended_city=f"{fake.postcode()} {fake.city()}",
            extended_street=fake.street_address(),
            user_id=user.id
        )
        db.session.add(user_personal_data)

    db.session.commit()

    # AUTHOR
    author_no_books = Author(full_name="Jan NoBooks")
    author_with_books = Author(full_name="Jan FewBooks")

    db.session.add_all([author_no_books, author_with_books])
    db.session.commit()

    categories = ["Fantasy", "IT", "Literature", "Math"]

    for _ in range(books):
        path = os.path.join(os.getcwd(), f"tests/images/{randint(1, 4)}.jpg")
        cover = open(path, "rb")
        book = Book(
            isbn=fake.isbn10(),
            title=fake.text(max_nb_chars=20)[:-1],
            description=fake.text(max_nb_chars=200),
            category=choice(categories),
            author_id=author_with_books.id,
            number_of_copies=fake.random_digit_not_null(),
            cover=cover.read(),
            publisher=fake.word().capitalize(),
            pages=fake.random_digit_not_null()*100,
            year=int(fake.year())
        )
        cover.close()
        db.session.add(book)
    db.session.commit()

    borrow = Borrow(user_id=test_user.id, book_id=book.id)
    db.session.add(borrow)
    db.session.commit()
    click.echo("Inserted test data.")

@click.command()
def test():
    import unittest
    tests = unittest.TestLoader().discover("tests")
    unittest.TextTestRunner(verbosity=2).run(tests)
