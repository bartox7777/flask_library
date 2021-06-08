from flask import render_template

from . import main


@main.route("/", methods=("GET", "POST"))
def search():
    return render_template("main/search.html", title="Panel wyszukiwania")