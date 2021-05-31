from flask import render_template

from . import auth
from .forms import LoginForm


@auth.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm()
    return render_template("auth/login.html", title="Login", form=form)