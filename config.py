import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    BABEL_DEFAULT_LOCALE = "pl"
    TESTING = True
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOOKS_PER_PAGE = 5
    USERS_PER_PAGE = 5
    MAX_PROLONG_TIMES = 1
    DEFAULT_BORROWING_DAYS = 14
    PROLONG_DAYS = 14
    MAX_CONTENT_LENGTH = 16 * 1000 * 1000  # 16 MB

    try:
        MAIL_SERVER = str(os.environ.get("MAIL_SERVER"))
        MAIL_PORT = int(os.environ.get("MAIL_PORT"))
        MAIL_USE_TLS = bool(int(os.environ.get("MAIL_USE_TLS")) or False)
        MAIL_USE_SSL = bool(int(os.environ.get("MAIL_USE_SSL")) or True)
        MAIL_USERNAME = str(os.environ.get("MAIL_USERNAME"))
        MAIL_PASSWORD = str(os.environ.get("MAIL_PASSWORD"))
        MAIL_DEFAULT_SENDER = str(
            os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get("MAIL_USERNAME")
        )
    except:
        raise Exception("Not properly set email settings.")

    # @staticmethod
    # def init_app(app):
    #     """ child classes could override this method
    #     and make some init actions """
    #     """ it's called in app factory """
    #     pass


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "data.sqlite")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")
    # SQLALCHEMY_ECHO = True
    SQLALCHEMY_RECORD_QUERIES = True
    BOOKS_PER_PAGE = 5


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URI") or "sqlite://"
    WTF_CSRF_ENABLED = False


config = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=ProductionConfig,
)
