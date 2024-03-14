__all__ = ["User", "PersonalData", "Permission", "Role", "Book", "Author", "Borrow"]

from flask_login import UserMixin

from datetime import datetime

from . import db
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    personal_data = db.relationship(
        "PersonalData", backref="user", cascade="all, delete-orphan"
    )
    password_hash = db.Column(db.String, nullable=False)
    activated = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    borrows = db.relationship("Borrow", backref="user", cascade="all, delete-orphan")

    def is_active(self):
        return self.activated

    @property
    def password(self):
        raise AttributeError("It is write only attribute.")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, permission):
        if self.role and (self.role.permissions & permission == permission):
            return True
        return False

    @property
    def full_name(self):
        return f"{self.personal_data[0].name} {self.personal_data[0].surname}"


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

    @staticmethod
    def insert_roles():
        roles = dict(
            anonymous=[],
            user=[Permission.USER],
            moderator=[Permission.USER, Permission.MODERATOR],
            admin=[Permission.USER, Permission.MODERATOR, Permission.ADMIN],
        )
        for name, permissions in roles.items():
            role = Role(name=name, permissions=sum(permissions))
            db.session.add(role)
        db.session.commit()


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    category = db.Column(db.String)
    description = db.Column(db.Text)
    author_id = db.Column(db.String, db.ForeignKey("author.id"), nullable=False)
    add_date = db.Column(db.DateTime, default=datetime.utcnow)
    number_of_copies = db.Column(db.Integer, nullable=False)
    cover = db.Column(db.LargeBinary)
    publisher = db.Column(db.String)
    pages = db.Column(db.Integer)
    year = db.Column(db.Integer)
    borrows = db.relationship("Borrow", backref="book", cascade="all, delete-orphan")


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String, nullable=False)
    books = db.relationship("Book", backref="author")


class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    prolong_times = db.Column(db.Integer, default=0, nullable=False)
    predicted_return_date = db.Column(db.DateTime(), nullable=False)
    return_date = db.Column(db.DateTime, default=None)
