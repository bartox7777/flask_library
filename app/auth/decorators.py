from flask import abort

from functools import wraps
from flask_login import current_user
from flask_login import login_required

from ..models import Permission


def moderator_required(view):
    @login_required
    @wraps(view)
    def check_permissions(*args, **kwargs):
        if not current_user.can(Permission.MODERATOR):
            abort(403)
        return view(*args, **kwargs)
    return check_permissions