import unittest

from app.models import Role
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