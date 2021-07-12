import unittest

from flask import current_app
from flask_login import current_user

from app import create_app


class ModerateTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        cli = self.app.test_cli_runner()
        cli.invoke(args=["init-db"])
        cli.invoke(args=["insert-test-data", "--books", str(current_app.config["BOOKS_PER_PAGE"] * 2)])
        self.client = self.app.test_client(use_cookies=True)

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
        # TODO: rest of test