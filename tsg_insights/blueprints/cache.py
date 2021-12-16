import json

from flask import Blueprint, jsonify, render_template, request

from ..data.cache import delete_from_cache, get_cache
from ..data.process import fetch_geocodes
from .fetch import get_registry_file

bp = Blueprint("cache", __name__)


@bp.route("/redis_cache")
def check_redis_cache():
    r = get_cache()
    cache_contents = {
        "keys": {x.decode("utf8"): r.type(x).decode("utf8") for x in r.keys()},
        "files": {
            k.decode("utf8"): json.loads(v.decode("utf8"))
            for k, v in r.hgetall("files").items()
        },
    }
    return json.dumps(cache_contents)


@bp.route("/reload/", methods=("GET", "POST"))
def reload_file():
    context = {}

    if request.method == "POST":
        file_id = request.form["fileid"]
        delete_from_cache(file_id)
        ret = get_registry_file(file_id)

        context["job"] = ret.data.decode("utf-8")
        context["file_id"] = file_id

    return render_template("cache_reloader.html.j2", **context)


@bp.route("/geocodes")
def view_geocodes():
    cache = get_cache()
    return jsonify(
        {k.decode("utf8"): c.decode("utf8") for k, c in cache.hscan_iter("geocodes")}
    )
