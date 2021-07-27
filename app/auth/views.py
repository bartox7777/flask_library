
from flask import flash
from flask import url_for
from flask import request
from flask import redirect
from flask import render_template

from flask_login import login_user
from flask_login import logout_user
from flask_login import current_user
from flask_login import login_required
from flask_login import fresh_login_required

from app import db
from . import auth
from ..models import User
from .forms import LoginForm
from .forms import ChangePasswordForm


@auth.route("/login", methods=("GET", "POST"))
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm(request.form)
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and user.verify_password(password):
            login_user(user)
            personal_data = user.personal_data[0]
            name, surname = personal_data.name, personal_data.surname
            flash(f"Użytkownik {name} {surname} zalogowany pomyślnie.", "success")

            next = request.args.get("next") # HACK: is next always safe?

            return redirect(next or url_for("main.index"))

        form.password.data = ""
        flash("Nieprawidłowe dane logowania.", "warning")


    return render_template("auth/login.html",
        title="Login",
        form=form,
        dont_show_navbar=True,
        dont_show_search_bar=True
    )

@auth.route("/logout", methods=("GET", "POST"))
@login_required
def logout():
    flash("Pomyślnie wylogowano.", "success")
    logout_user()
    return redirect(url_for("main.index"))

@auth.route("/change-password", methods=("GET", "POST"))
@fresh_login_required
def change_password():
    form = ChangePasswordForm(request.form)

    if form.validate_on_submit():
        current_user.password = form.password.data
        db.session.commit()
        flash("Zmiana hasła przebiegła pomyślnie.", category="success")

    return render_template(
        "auth/change_password.html",
        title="Zmiana hasła",
        password_form=form,
        dont_show_search_bar=True
    )