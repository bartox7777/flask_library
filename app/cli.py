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
@click.option("--additional-users", default=10, help="Number of additional users.")
@with_appcontext
def insert_test_data(additional_users):
    # USER
    role_user_id = Role.query.filter_by(name="user").first().id
    role_moderator_id = Role.query.filter_by(name="moderator").first().id
    role_admin_id = Role.query.filter_by(name="admin").first().id

    test_admin = User(email="test@test.admin", password="test", activated=True, role_id=role_admin_id)
    test_moderator = User(email="test@test.moderator", password="test", activated=True, role_id=role_moderator_id)
    test_user = User(email="test@test.user", password="test", activated=True, role_id=role_user_id)
    test_user_inactive = User(email="test@test.user-inactive", password="test", activated=False, role_id=role_user_id)

    db.session.add_all([test_admin, test_moderator, test_user, test_user_inactive])

    # PERSONAL DATA
    fake = Faker()
    for _ in range(additional_users):
        user = User(email=fake.unique.ascii_email(), password="test", activated=True, role_id=role_user_id)
        db.session.add(user)
    fake.unique.clear()

    db.session.commit()

    for user in User.query.all():
        user_personal_data = PersonalData(
            name=fake.first_name(),
            surname=fake.last_name(),
            phone_number=fake.phone_number(),
            extended_city=f"{fake.postcode()} {fake.city()}",
            extended_street=fake.street_address(),
            user_id=user.id
        )
        db.session.add(user_personal_data)

    db.session.commit()