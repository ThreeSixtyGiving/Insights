import os

from flask import Blueprint
from flask import current_app as app
from flask import jsonify, render_template

from ..data.registry import process_registry

bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    registry = process_registry(None, app.config.get("THREESIXTY_STATUS_JSON"))
    return render_template("index.html.j2", registry=registry)


@bp.route("/about")
def about():
    return render_template("about.html.j2")
