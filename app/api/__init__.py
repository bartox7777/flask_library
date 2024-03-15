from flask import Blueprint


api = Blueprint("api", __name__, url_prefix="/api")


from . import auth
from . import main
from . import moderate