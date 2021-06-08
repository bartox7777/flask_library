import unittest
import random

from app.models import *
from app import create_app


class CLITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.runner = self.app.test_cli_runner()

    def tearDown(self):
        self.app_context.pop()

    def test_init_db(self):
        result = self.runner.invoke(args=["init-db", "--test"])
        self.assertTrue("Database initialized." == result.output.strip())

        roles = ["user", "moderator", "admin"]
        for role in roles:
            fetched_role = Role.query.filter_by(name=role).first()
            self.assertIsNotNone(fetched_role)

    def test_insert_test_data(self):
        additional_users_number = random.randint(20, 50)
        books_number = random.randint(10, 30)

        self.runner.invoke(args=["init-db", "--test"])
        self.runner.invoke(args=["insert-test-data", "--additional-users", additional_users_number, "--books", books_number])

        random_user = random.choice(User.query.all())
        self.assertTrue(User.query.count() == additional_users_number+4)
        self.assertTrue(User.query.filter_by(activated=False, email="test@test.user-inactive").count() == 1)
        self.assertTrue(random_user.personal_data)
        random_user_personal_data = random_user.personal_data[0]
        self.assertIsNotNone(random_user_personal_data.name)
        self.assertIsNotNone(random_user_personal_data.surname)
        self.assertIsNotNone(random_user_personal_data.phone_number)
        self.assertIsNotNone(random_user_personal_data.extended_city)
        self.assertIsNotNone(random_user_personal_data.extended_street)

        self.assertTrue(Book.query.count() == books_number)
        random_book = random.choice(Book.query.all())
        self.assertIsNotNone(random_book.isbn)
        self.assertIsNotNone(random_book.title)
        self.assertIsNotNone(random_book.description)
        self.assertIsNotNone(random_book.author_id)
        self.assertIsNotNone(random_book.number_of_copies)
        self.assertIsNotNone(random_book.publisher)
        self.assertIsNotNone(random_book.pages)
        self.assertIsNotNone(random_book.year)

        self.assertTrue(random_book.author)
        random_book_author = random_book.author
        self.assertTrue(random_book_author.full_name == "Jan FewBooks")

        author_no_books = Author.query.filter_by(full_name="Jan NoBooks").first()
        self.assertIsNotNone(author_no_books)
        self.assertFalse(author_no_books.books)

        test_user = User.query.filter_by(email="test@test.user").first()
        self.assertTrue(len(test_user.borrows) == 1)
        test_user_borrow = test_user.borrows[0]
        self.assertIsNotNone(test_user_borrow.date)
        self.assertEqual(test_user_borrow.prolong_times, 0)
        self.assertIsNone(test_user_borrow.return_date)
        self.assertTrue(test_user_borrow.book)
