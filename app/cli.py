from flask.cli import with_appcontext

import click
from faker import Faker

from . import db
from .models import *
from flask_migrate import init
from flask_migrate import migrate
from flask_migrate import upgrade


@click.command()
@with_appcontext
def init_db():
    init()
    migrate()
    upgrade()

    Role.insert_roles()

    click.echo("Database initialized.")

@click.command()
@with_appcontext
def insert_fake_data():
    fake = Faker()
    role_user_id = Role.query.filter_by(name="user").first().id
    role_moderator_id = Role.query.filter_by(name="moderator").first().id
    role_admin_id = Role.query.filter_by(name="admin").first().id

    test_admin = User(email="test@test.admin", password="test", activated=True, role_id=role_admin_id)
    test_moderator = User(email="test@test.moderator", password="test", activated=True, role_id=role_moderator_id)
    test_user = User(email="test@test.user", password="test", activated=True, role_id=role_user_id)

    db.session.add_all([test_admin, test_moderator, test_user])
    db.session.commit()

    # TODO insert random users