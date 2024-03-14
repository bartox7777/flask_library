from flask import flash, get_flashed_messages, jsonify

from functools import wraps
from flask_login import current_user

from ..models import Permission


def login_required_api(view):
    @wraps(view)
    def is_authenticated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Musisz być zalogowany, aby wykonać tę akcję.", "warning")
            return jsonify({"flashes": get_flashed_messages()}), 401
        return view(*args, **kwargs)

    return is_authenticated


def moderator_required_api(view):
    @login_required_api
    @wraps(view)
    def check_permissions(*args, **kwargs):
        if not current_user.can(Permission.MODERATOR):
            flash(
                "Musisz mieć uprawnienia moderatora, aby wykonać tę akcję.", "warning"
            )
            return jsonify({"flashes": get_flashed_messages()}), 401
        return view(*args, **kwargs)

    return check_permissions


def admin_required_api(view):
    @login_required_api
    @wraps(view)
    def check_permissions(*args, **kwargs):
        if not current_user.can(Permission.ADMIN):
            flash(
                "Musisz mieć uprawnienia administratora, aby wykonać tę akcję.",
                "warning",
            )
            return jsonify({"flashes": get_flashed_messages()}), 401
        return view(*args, **kwargs)

    return check_permissions
