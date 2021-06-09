import unittest

from flask_login import current_user

from app import create_app
from app.models import User


class ClientTestCase(unittest.TestCase):
    pass
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        cli = self.app.test_cli_runner()
        cli.invoke(args=["init-db"])
        cli.invoke(args=["insert-test-data"])
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        self.app_context.pop()

    def test_search_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # TODO: check some keyword from page

    def test_auth_pages(self):
        response = self.client.post("/login", data=dict(
            email="test@test.user",
            password="test"),
            follow_redirects=True
        )
        # TODO: is it possible to use current_user?
        self.assertEqual(response.status_code, 200)
        test_user = User.query.filter_by(email="test@test.user").first()
        full_name = test_user.personal_data[0].name + " " + test_user.personal_data[0].surname
        self.assertTrue(full_name in response.get_data(as_text=True))
