from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_login import AnonymousUserMixin
from flask_babel import Babel
from flask_migrate import Migrate
from flask_mail import Mail

from config import config


db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
migrate = Migrate()
mail = Mail()

# is it good solution?
class AnonymousUser(AnonymousUserMixin):
    role = dict(
        name="anonymous"
    )
    # TODO: role = Role.query.filter_by(name="anonymous").first()

login_manager.login_view = "auth.login"
login_manager.login_message = "Zaloguj się, aby mieć dostęp do tej strony."
login_manager.login_message_category = "warning"
login_manager.anonymous_user = AnonymousUser

def create_app(config_name="production"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # config_name[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    from . import models
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    @app.shell_context_processor
    def shell_context():
        return dict(
            db = db,
            User = models.User,
            Role = models.Role,
            PersonalData = models.PersonalData,
            Author = models.Author,
            Book = models.Book,
            Borrow = models.Borrow
        )

    from .cli import init_db
    from .cli import insert_test_data
    from .cli import test
    app.cli.add_command(init_db)
    app.cli.add_command(insert_test_data)
    app.cli.add_command(test)


    from .auth import auth
    from .main import main
    from .moderate import moderate
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(moderate)

    return app
