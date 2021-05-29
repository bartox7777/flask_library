from flask import g
from flask_sqlalchemy import SQLAlchemy


def get_db():
    pass
    # if "db" not in g:
    #     g.db = SQLAlchemy