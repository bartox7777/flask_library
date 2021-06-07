from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel
from flask_migrate import Migrate

from config import config


db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
migrate = Migrate()

def create_app(config_name="production"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # config_name[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    migrate.init_app(app, db)

    from . import models
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    from .cli import init_db
    from .cli import insert_test_data
    from .cli import test
    app.cli.add_command(init_db)
    app.cli.add_command(insert_test_data)
    app.cli.add_command(test)


    from .auth import auth
    from .main import main
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.add_url_rule("/", endpoint="main.index")

    return app
