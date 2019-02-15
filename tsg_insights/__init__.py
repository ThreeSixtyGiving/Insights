import os

from flask import Flask, send_from_directory
from flask.json import JSONEncoder
import pandas as pd

from .data.registry import THREESIXTY_STATUS_JSON

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        JSON_SORT_KEYS=False,

        # Newsletter
        NEWSLETTER_FORM_ACTION=os.environ.get("NEWSLETTER_FORM_ACTION"),
        NEWSLETTER_FORM_U=os.environ.get("NEWSLETTER_FORM_U"),
        NEWSLETTER_FORM_ID=os.environ.get("NEWSLETTER_FORM_ID"),

        # 360Giving registry URL
        THREESIXTY_STATUS_JSON=os.environ.get(
            "THREESIXTY_STATUS_JSON", THREESIXTY_STATUS_JSON),

        # Mapbox maps
        MAPBOX_ACCESS_TOKEN=os.environ.get("MAPBOX_ACCESS_TOKEN"),
        MAPBOX_STYLE=os.environ.get("MAPBOX_STYLE"),

        # Redis variables - not set here
        # REDIS_DEFAULT_URL='redis://localhost:6379/0' # default URL for redis instance
        # REDIS_ENV_VAR='REDIS_URL'                    # name of the environmental variable that will be looked up for the redis url
        # CACHE_DEFAULT_PREFIX='file_'
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # overwrite default JSON encoder
    app.json_encoder = CustomJSONEncoder

    from .blueprints import home, fetch, job, data, cache
    app.register_blueprint(home.bp)
    app.register_blueprint(fetch.bp, url_prefix='/fetch')
    app.register_blueprint(job.bp, url_prefix='/job')
    app.register_blueprint(data.bp, url_prefix='/data')
    app.register_blueprint(cache.bp, url_prefix='/cache')
    app.add_url_rule('/', endpoint='index')

    @app.route('/images/<path:path>')
    def send_images(path):
        return send_from_directory('static/images', path)

    return app


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        # handling numpy numbers:
        if isinstance(obj, pd.np.generic):
            return pd.np.asscalar(obj)

        # handling pandas dataframes:
        if isinstance(obj, (pd.Series, pd.DataFrame)):

            # handling dataframes with multiindex
            if isinstance(obj.index, pd.core.index.MultiIndex):
                obj.index = obj.index.map(" - ".join)
            return obj.to_dict()

        # else let the base class do the work
        return JSONEncoder.default(self, obj)
