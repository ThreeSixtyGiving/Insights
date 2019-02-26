import json

from flask import Blueprint, jsonify, request

from ..data.cache import get_cache
from ..data.process import fetch_geocodes

bp = Blueprint('cache', __name__)


@bp.route('/redis_cache')
def check_redis_cache():
    r = get_cache()
    cache_contents = {
        "keys": {
            x.decode('utf8'): r.type(x).decode('utf8') for x in r.keys()
        },
        "files": {
            k.decode('utf8'): json.loads(v.decode('utf8')) for k, v in r.hgetall("files").items()
        }
    }
    return json.dumps(cache_contents)

@bp.route('/geocodes')
def view_geocodes():
    cache = get_cache()
    return jsonify({
        k.decode("utf8"): c.decode("utf8")
        for k, c in cache.hscan_iter("geocodes")
    })
