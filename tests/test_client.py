import re
import unittest
import random


from flask import current_app
from flask_login import current_user

from app import create_app
from app import login_manager
from app.models import Book, Borrow

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
            full_name = f"{current_user.full_name}"
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

    def test_book_details(self):
        random_book = random.choice(Book.query.all())
        response = self.client.get(f"/book-details/{random_book.id}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse('title="Wypożycz"' in response.get_data(as_text=True))
        self.assertFalse('title="Edytuj"' in response.get_data(as_text=True))

        self.assertTrue(random_book.title in response.get_data(as_text=True))
        self.assertTrue(random_book.author.full_name in response.get_data(as_text=True))
        self.assertTrue(str(random_book.year) in response.get_data(as_text=True))
        self.assertTrue(str(random_book.pages) in response.get_data(as_text=True))
        self.assertTrue(random_book.category in response.get_data(as_text=True))
        self.assertTrue(random_book.description[:20] in response.get_data(as_text=True))

        with self.client as client:
            client.post("/login", data=dict(
                email="test@test.user",
                password="test"),
                follow_redirects=True)

            random_book = random.choice(Book.query.all())
            response = self.client.get(f"/book-details/{random_book.id}")
            self.assertEqual(response.status_code, 200)
            self.assertFalse('title="Wypożycz"' in response.get_data(as_text=True))
            self.assertFalse('title="Edytuj"' in response.get_data(as_text=True))

            response = client.get("/logout", follow_redirects=True)
            client.post("/login", data=dict(
                email="test@test.moderator",
                password="test"),
                follow_redirects=True)

            random_book = random.choice(Book.query.all())
            response = self.client.get(f"/book-details/{random_book.id}")
            self.assertEqual(response.status_code, 200)
            self.assertTrue('title="Wypożycz"' in response.get_data(as_text=True))
            self.assertTrue('title="Edytuj"' in response.get_data(as_text=True))

            response = client.get("/logout", follow_redirects=True)
            client.post("/login", data=dict(
                email="test@test.admin",
                password="test"),
                follow_redirects=True)

            random_book = random.choice(Book.query.all())
            response = self.client.get(f"/book-details/{random_book.id}")
            self.assertEqual(response.status_code, 200)
            self.assertTrue('title="Wypożycz"' in response.get_data(as_text=True))
            self.assertTrue('title="Edytuj"' in response.get_data(as_text=True))

    def test_borrowed_books(self):
        with self.client as client:
            response = client.get("/borrowed-books")
            self.assertEqual(response.status_code, 302)

            client.post("/login", data=dict(
                email="test@test.user",
                password="test"),
                follow_redirects=True)
            response = client.get("/borrowed-books")
            self.assertEqual(response.status_code, 200)
            borrow = Borrow.query.filter_by(user_id=current_user.id).first()
            self.assertTrue(borrow.book.title in response.get_data(as_text=True))
            self.assertTrue(borrow.book.isbn in response.get_data(as_text=True))
            self.assertTrue('title="Prolonguj wypożyczenie"' in response.get_data(as_text=True))