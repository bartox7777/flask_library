from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import LoginManager

from config import config


db = SQLAlchemy()
bootstrap = Bootstrap()

login_manager = LoginManager()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # config_name[config_name].init_app(app)

    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)

    return app
