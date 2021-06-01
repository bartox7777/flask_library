import os


basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    BABEL_DEFAULT_LOCALE = "pl"
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # @staticmethod
    # def init_app(app):
    #     """ child classes could override this method
    #     and make some init actions """
    #     """ it's called in app factory """
    #     pass


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URI") or \
        "sqlite:///" + os.path.join(basedir, "data.sqlite")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URI") or \
        "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_RECORD_QUERIES = True


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