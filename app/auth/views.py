from flask import g
from flask import flash
from flask import url_for
from flask import session
from flask import redirect
from flask import render_template

from . import auth
from ..models import User
from .forms import LoginForm


@auth.before_app_request
def load_logged_user():
    user_id = session.get("user_id")

    if user_id:
        g.user = User.query.get(user_id)
    else:
        g.user = None

@auth.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and user.verify_password(password):
            personal_data = user.personal_data[0]
            name, surname = personal_data.name, personal_data.surname
            flash(f"Użytkownik {name} {surname} zalogowany pomyślnie.", "success")
            return redirect(url_for("main.search"))

        form.password.data = ""
        flash("Nieprawidłowe dane logowania.", "warning")


    return render_template("auth/login.html", title="Login", form=form)