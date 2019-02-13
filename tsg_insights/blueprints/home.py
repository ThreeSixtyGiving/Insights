import os

from flask import Blueprint, render_template, jsonify

from ..data.registry import process_registry
from ..data.cache import get_from_cache

bp = Blueprint('home', __name__)

@bp.route('/')
def index():
    registry = process_registry()
    newsletter = dict(
        form_action=os.environ.get("NEWSLETTER_FORM_ACTION"),
        form_u=os.environ.get("NEWSLETTER_FORM_U"),
        form_id=os.environ.get("NEWSLETTER_FORM_ID"),
    )
    return render_template('index.html.j2', registry=registry, newsletter=newsletter)
