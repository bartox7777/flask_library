from sqlalchemy.orm import query
from app.main.views import search
import unittest

from flask import current_app
from flask_login import current_user

from app import create_app
from app import login_manager
from app.models import Book

class ClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        cli = self.app.test_cli_runner()
        cli.invoke(args=["init-db"])
        # two pagination pages
        cli.invoke(args=["insert-test-data", "--books", str(current_app.config["BOOKS_PER_PAGE"] * 2)])
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"Zaloguj" in response.get_data())
        self.assertTrue("Ostatnio dodane książki" in response.get_data(as_text=True))
        last_added_books = Book.query.order_by(Book.add_date.desc()).limit(5).all()
        for book in last_added_books:
            self.assertTrue(book.title in response.get_data(as_text=True))

        response = self.client.get("/", query_string=dict(
            phrase = "help"
        ))
        self.assertEqual(response.status_code, 200)

    def test_search_page(self):
        with self.client as client:
            response = client.get("/search", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Znalezione książki" in response.get_data(as_text=True))

            response = client.get("/search", data=dict(page=2), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            response = client.get("/search", query_string=dict(page=3), follow_redirects=True)
            self.assertEqual(response.status_code, 404)

            response = client.get("/search", follow_redirects=True)
            first_book = Book.query.first()
            self.assertTrue(first_book.title in response.get_data(as_text=True))

            response = client.get("/search", query_string=dict(
                    phrase="//@@!!thiscannotbesearched??..\\\\",
                ),
                follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"Nic nie znaleziono..." in response.get_data())

    def test_auth_pages(self):
        with self.client as client:
            response = client.get("/logout", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(login_manager.login_message in response.get_data(as_text=True))

        with self.client as client:
            response = client.post("/login", data=dict(
            email="test@test.user",
            password="test"),
            follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            full_name = f"{current_user.personal_data[0].name} {current_user.personal_data[0].surname}"
            self.assertTrue(full_name in response.get_data(as_text=True))
            self.assertTrue(b"Wyloguj" in response.get_data())

            response = client.get("/logout", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Pomyślnie wylogowano." in response.get_data(as_text=True))
            self.assertTrue(b"Zaloguj" in response.get_data())

            response = client.post("/login", data=dict(
            email="test@test.X",
            password="X"),
            follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Nieprawidłowe dane logowania." in response.get_data(as_text=True))
