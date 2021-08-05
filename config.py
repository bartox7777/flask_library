import os


basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    BABEL_DEFAULT_LOCALE = "pl"
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOOKS_PER_PAGE = 5
    USERS_PER_PAGE = 5
    MAX_PROLONG_TIMES = 1
    DEFAULT_BORROWING_DAYS = 14
    PROLONG_DAYS = 14
    MAX_CONTENT_LENGTH = 16 * 1000 * 1000  # 16 MB


    # @staticmethod
    # def init_app(app):
    #     """ child classes could override this method
    #     and make some init actions """
    #     """ it's called in app factory """
    #     pass


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI") or \
        "sqlite:///" + os.path.join(basedir, "data.sqlite")
    # MAIL_SERVER = str()
    # MAIL_PORT = int()
    # MAIL_USE_TLS = bool()
    # MAIL_USE_SSL = bool()
    # MAIL_USERNAME = str()
    # MAIL_PASSWORD = str()
    # MAIL_DEFAULT_SENDER = str()


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_DEFAULT_SENDER = "fake@mail.pl"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URI") or \
        "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")
    # SQLALCHEMY_ECHO = True
    SQLALCHEMY_RECORD_QUERIES = True
    BOOKS_PER_PAGE = 5


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URI") or \
        "sqlite://"
    WTF_CSRF_ENABLED = False


config = dict(
    development = DevelopmentConfig,
    testing = TestingConfig,
    production = ProductionConfig,

    default = ProductionConfig
)