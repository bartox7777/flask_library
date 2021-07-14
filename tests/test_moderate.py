import os
import unittest
from faker import Faker

from flask import current_app

from app import create_app
from app.models import Author
from app.models import Book

class ModerateTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        cli = self.app.test_cli_runner()
        cli.invoke(args=["init-db"])
        cli.invoke(args=["insert-test-data", "--books", str(current_app.config["BOOKS_PER_PAGE"] * 2)])
        self.client = self.app.test_client(use_cookies=True)
        self.fake = Faker()

    def tearDown(self):
        self.app_context.pop()

    def test_add_book(self):
        response = self.client.get("/add-book")
        self.assertEqual(response.status_code, 302)  # redirect to /login

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.user",
                password="test"),
                follow_redirects=True)
            response = client.get("/add-book", follow_redirects=True)
            self.assertEqual(response.status_code, 403)
            client.get("/logout", follow_redirects=True)

            response = client.post("/login", data=dict(
                email="test@test.moderator",
                password="test"),
                follow_redirects=True)
            response = client.get("/add-book", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            books_len = len(Book.query.all())
            response = client.post("/add-book", data=dict(
                isbn=self.fake.isbn10(),
                title=self.fake.text(max_nb_chars=20)[:-1],
                description=self.fake.text(max_nb_chars=500),
                category="fantasy",
                author=Author.query.filter_by(full_name="Jan FewBooks").first().id,
                number_of_copies=self.fake.random_digit_not_null(),
                publisher=self.fake.word().capitalize(),
                pages=self.fake.random_digit_not_null()*100,
                year=int(self.fake.year())
            ))
            self.assertEqual(response.status_code, 302)
            self.assertGreater(len(Book.query.all()), books_len)
            client.get("/logout", follow_redirects=True)

            response = client.post("/login", data=dict(
                email="test@test.admin",
                password="test"),
                follow_redirects=True)
            response = client.get("/add-book", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            books_len = len(Book.query.all())
            response = client.post("/add-book", data=dict(
                isbn=self.fake.isbn10(),
                title=self.fake.text(max_nb_chars=20)[:-1],
                description=self.fake.text(max_nb_chars=500),
                category="fantasy",
                author=Author.query.filter_by(full_name="Jan FewBooks").first().id,
                number_of_copies=self.fake.random_digit_not_null(),
                publisher=self.fake.word().capitalize(),
                pages=self.fake.random_digit_not_null()*100,
                year=int(self.fake.year())
            ))
            self.assertEqual(response.status_code, 302)
            self.assertGreater(len(Book.query.all()), books_len)