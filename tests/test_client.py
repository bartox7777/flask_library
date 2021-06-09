import unittest

from app import create_app


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
