from flask import current_app

import unittest
from faker import Faker
from random import choice
from flask_login import current_user

from app import create_app
from app.models import Author
from app.models import User
from app.models import Book
from app.models import Role
from app.models import Borrow


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

    def test_edit_book(self):
        random_book = choice(Book.query.all())
        author_name = random_book.author.full_name

        response = self.client.get(f"/edit-book/{random_book.id}")
        self.assertEqual(response.status_code, 302)

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.user",
                password="test"),
                follow_redirects=True)
            response = client.get(f"/edit-book/{random_book.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 403)
            client.get("/logout", follow_redirects=True)

            response = client.post("/login", data=dict(
                email="test@test.moderator",
                password="test"),
                follow_redirects=True)
            response = client.get(f"/edit-book/{random_book.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(random_book.isbn in response.get_data(as_text=True))
            self.assertTrue(random_book.title in response.get_data(as_text=True))
            self.assertTrue(random_book.category in response.get_data(as_text=True))
            self.assertTrue(random_book.description in response.get_data(as_text=True))
            self.assertTrue(random_book.author.full_name in response.get_data(as_text=True))
            self.assertTrue(str(random_book.number_of_copies) in response.get_data(as_text=True))
            self.assertTrue(random_book.publisher in response.get_data(as_text=True))
            self.assertTrue(str(random_book.pages) in response.get_data(as_text=True))
            self.assertTrue(str(random_book.year) in response.get_data(as_text=True))

            response = client.post(f"/edit-book/{random_book.id}", follow_redirects=True, data=dict(
                title="@testpurpose@",
                author=random_book.author_id
            ))
            self.assertTrue("@testpurpose@" in response.get_data(as_text=True))
            client.get("/logout", follow_redirects=True)

            response = client.post("/login", data=dict(
                email="test@test.admin",
                password="test"),
                follow_redirects=True)
            response = client.get(f"/edit-book/{random_book.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(random_book.isbn in response.get_data(as_text=True))
            self.assertTrue(random_book.title in response.get_data(as_text=True))
            self.assertTrue(random_book.category in response.get_data(as_text=True))
            self.assertTrue(random_book.description in response.get_data(as_text=True))
            self.assertTrue(author_name in response.get_data(as_text=True))
            self.assertTrue(str(random_book.number_of_copies) in response.get_data(as_text=True))
            self.assertTrue(random_book.publisher in response.get_data(as_text=True))
            self.assertTrue(str(random_book.pages) in response.get_data(as_text=True))
            self.assertTrue(str(random_book.year) in response.get_data(as_text=True))

            response = client.post(f"/edit-book/{random_book.id}", follow_redirects=True, data=dict(
                title="!testpurpose!",
                author=random_book.author_id
            ))
            self.assertTrue("!testpurpose!" in response.get_data(as_text=True))
            client.get("/logout", follow_redirects=True)

    def test_borrow_book(self):
        random_book = choice(Book.query.all())
        response = self.client.get(f"/borrow-book/{random_book.id}")
        self.assertEqual(response.status_code, 302)

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.user",
                password="test"),
                follow_redirects=True)
            response = self.client.get(f"/borrow-book/{random_book.id}")
            self.assertEqual(response.status_code, 403)
            client.get("/logout", follow_redirects=True)

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.moderator",
                password="test"),
                follow_redirects=True)
            response = client.get(f"/borrow-book/{random_book.id}")
            self.assertEqual(response.status_code, 200)

            user_id = User.query.filter_by(email="test@test.user").first().id
            for _ in range(random_book.number_of_copies):
                response = client.post(f"/borrow-book/{random_book.id}", follow_redirects=True, data=dict(
                    user_id=user_id
                ))
            borrows = [borrow for borrow in random_book.borrows if borrow.return_date is None and borrow.user_id==user_id]
            self.assertEqual(len(borrows), random_book.number_of_copies)
            client.get("/logout", follow_redirects=True)

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.admin",
                password="test"),
                follow_redirects=True)
            response = client.get(f"/borrow-book/{random_book.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Brak dostępnych kopii do wypożyczenia" in response.get_data(as_text=True))
            self.assertTrue(f"0 / {random_book.number_of_copies}" in response.get_data(as_text=True))

    def test_add_user(self):
        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.user",
                password="test"),
                follow_redirects=True)
            response = client.get("/add-user")
            self.assertEqual(response.status_code, 403)
            client.get("/logout", follow_redirects=True)

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.moderator",
                password="test"),
                follow_redirects=True)
            response = client.post("/add-user", data=dict(
                name="test",
                surname="test",
                phone_number="123123123",
                extended_city="poznan",
                extended_street="dabrowskiego",
                email="test@test.user",
                role=Role.query.filter_by(name="user").first().id
            ))
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Ten email jest już przypisany." in response.get_data(as_text=True))

            response = client.post("/add-user", data=dict(
                name="test",
                surname="test",
                phone_number="123123123",
                extended_city="poznan",
                extended_street="dabrowskiego",
                email="test@test.newuser",
                role=Role.query.filter_by(name="user").first().id
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Użytkownik test test dodany pomyślnie." in response.get_data(as_text=True))
            self.assertTrue(User.query.filter_by(email="test@test.newuser").first())
            client.get("/logout", follow_redirects=True)

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.admin",
                password="test"),
                follow_redirects=True)

            response = client.post("/add-user", data=dict(
                name="test",
                surname="test",
                phone_number="321321321",
                extended_city="ec",
                extended_street="es",
                email="test@test.neweruser",
                role=Role.query.filter_by(name="user").first().id
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Użytkownik test test dodany pomyślnie." in response.get_data(as_text=True))
            self.assertTrue(User.query.filter_by(email="test@test.neweruser").first())
            client.get("/logout", follow_redirects=True)

    def test_edit_user(self):
        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.user",
                password="test"),
                follow_redirects=True)
            response = client.get(f"/edit-user/{current_user.id}")
            self.assertEqual(response.status_code, 403)
            client.get("/logout", follow_redirects=True)

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.moderator",
                password="test"),
                follow_redirects=True)

            user = User.query.filter_by(email="test@test.user").first()
            response = client.get(f"/edit-user/{user.id}")
            self.assertTrue(user.personal_data[0].name in response.get_data(as_text=True))
            self.assertTrue(user.personal_data[0].surname in response.get_data(as_text=True))
            self.assertTrue(user.personal_data[0].phone_number in response.get_data(as_text=True))
            self.assertTrue(user.personal_data[0].extended_city in response.get_data(as_text=True))
            self.assertTrue(user.personal_data[0].extended_street in response.get_data(as_text=True))
            self.assertTrue(user.email in response.get_data(as_text=True))

            response = client.post(f"/edit-user/{user.id}", data=dict(
                name="test",
                surname="testing",
                phone_number=user.personal_data[0].phone_number,
                extended_city="ec",
                extended_street="es",
                email=user.email,
                activated=True,
                role=user.role_id
            ), follow_redirects=True)

            self.assertEqual(user.full_name, "test testing")

    def test_prolong_borrow(self):
        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.moderator",
                password="test"),
                follow_redirects=True)

            borrow = Borrow.query.first()

            response = client.get(f"/prolong-borrow/{borrow.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Pomyślnie przedłużono wypożyczenie." in response.get_data(as_text=True))

            response = client.get(f"/prolong-borrow/{borrow.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Wykorzystano maksymalną liczbę przedłużeń" in response.get_data(as_text=True))

    def test_return_book(self):
        borrow = Borrow.query.first()

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.user",
                password="test"),
                follow_redirects=True)
            response = client.get(f"/return-book/{borrow.id}")
            self.assertEqual(response.status_code, 403)
            client.get("/logout")

        with self.client as client:
            response = client.post("/login", data=dict(
                email="test@test.moderator",
                password="test"),
                follow_redirects=True)
            self.assertIsNone(borrow.return_date)
            response = client.get(f"/return-book/{borrow.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Zwrot książki przebiegł pomyślnie." in response.get_data(as_text=True))
            self.assertIsNotNone(borrow.return_date)

            response = client.get(f"/return-book/{borrow.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Ta książka została już zwrócona." in response.get_data(as_text=True))