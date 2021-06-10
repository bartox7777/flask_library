import unittest

from flask_login import current_user


from app import create_app
from app import login_manager

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
        self.assertTrue(b"Zaloguj" in response.get_data())

    def test_auth_pages(self):
        with self.client as client:
            response = client.get("logout", follow_redirects=True)
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

            response = client.get("logout", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Pomyślnie wylogowano." in response.get_data(as_text=True))
            self.assertTrue(b"Zaloguj" in response.get_data())

            response = client.post("/login", data=dict(
            email="test@test.X",
            password="X"),
            follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Nieprawidłowe dane logowania." in response.get_data(as_text=True))
