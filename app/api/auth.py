from flask import flash
from flask import get_flashed_messages
from flask import jsonify
from flask import request

import datetime
from flask_login import login_user
from flask_login import logout_user

from app.api.decorators import login_required_api

from . import api
from app import db
from ..models import User
from ..models import Borrow
from flask_login import current_user


@api.route("/login", methods=(["POST"]))
def login():
    if current_user.is_authenticated:
        flash("Jesteś już zalogowany.", "warning")
        return jsonify({"flashes": get_flashed_messages(with_categories=True)()})

    email = request.args.get("email")
    password = request.args.get("password")

    user = User.query.filter_by(email=email).first()
    if user and user.verify_password(password):
        login_user(user)
        personal_data = user.personal_data[0]
        name, surname = personal_data.name, personal_data.surname
        flash(f"Użytkownik {name} {surname} zalogowany pomyślnie.", "success")

        delayed_borrows = Borrow.query.filter(
            Borrow.return_date is None,
            Borrow.predicted_return_date <= datetime.datetime.now(),
        ).count()

        if delayed_borrows > 0:
            flash("Czas na zwrot niektórych książek.", "warning")

        return jsonify({"flashes": get_flashed_messages(with_categories=True)()})

    flash("Nieprawidłowe dane logowania.", "warning")

    return jsonify({"flashes": get_flashed_messages(with_categories=True)()})


@api.route("/logout", methods=(["POST"]))
@login_required_api
def logout():
    flash("Pomyślnie wylogowano.", "success")
    logout_user()
    return jsonify({"flashes": get_flashed_messages(with_categories=True)()})


@api.route("/change-password", methods=(["POST"]))
@login_required_api
def change_password():
    if request.args.get("password") != request.args.get("repeated_password"):
        flash("Hasła nie są takie same.", "warning")

    elif len(request.args.get("password")) < 4:
        flash("Hasło musi mieć co najmniej 4 znaki.", "warning")

    else:
        current_user.password = request.args.get("password")
        current_user.activated = True
        db.session.commit()
        flash("Zmiana hasła przebiegła pomyślnie.", "success")

    return jsonify({"flashes": get_flashed_messages(with_categories=True)()})
