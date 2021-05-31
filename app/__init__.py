from flask import Flask
from flask import redirect
from flask import url_for

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import config


db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name="production"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # config_name[config_name].init_app(app)

    db.init_app(app)
    # login_manager.init_app(app)

    @app.route("/")
    def redirect_to_login():
        return redirect(url_for("auth.login"))

    from .auth import auth

    app.register_blueprint(auth)

    # app.add_url_rule("/", endpoint="auth.login")

    return app
