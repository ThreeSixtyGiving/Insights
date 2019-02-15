import os

from flask import Blueprint, render_template, jsonify
from flask import current_app as app

from ..data.registry import process_registry
from ..data.cache import get_from_cache

bp = Blueprint('home', __name__)

@bp.route('/')
def index():
    registry = process_registry(None, app.config.get("THREESIXTY_STATUS_JSON"))
    newsletter = dict(
        form_action=app.config.get("NEWSLETTER_FORM_ACTION"),
        form_u=app.config.get("NEWSLETTER_FORM_U"),
        form_id=app.config.get("NEWSLETTER_FORM_ID"),
    )
    return render_template('index.html.j2', registry=registry, newsletter=newsletter)
