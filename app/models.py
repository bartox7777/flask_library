from flask_login import UserMixin

import datetime

from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    personal_data = db.relationship("PersonalData", backref="user")
    password = db.Column(db.String, nullable=False)
    activated = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


class PersonalData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, unique=True)
    extended_city = db.Column(db.String)  # city with postal code
    extended_street = db.Column(db.String)  # street with home number
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Permission:
    USER = 1
    MODERATOR = 2
    ADMIN = 4


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    permissions = db.Column(db.Integer, nullable=False)
    users = db.relationship("User", backref="role")


class Book(db.Model):
    isbn = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    category = db.Column(db.String)
    author = db.Column(db.String, db.ForeignKey("author.id"), nullable=False)
    publisher = db.Column(db.String)
    pages = db.Column(db.Integer)





class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.isbn"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    prolong_times = db.Column(db.Integer, default=datetime.utcnow, nullable=False)
