# -*- coding: utf-8 -*-
import dash
from flask import render_template

from tsg_insights import create_app

server = create_app()

scripts = []
analytics_script = ''
if server.config.get("GOOGLE_ANALYTICS_TRACKING_ID"):
    scripts.append("https://www.googletagmanager.com/gtag/js?id={}".format(
        server.config.get("GOOGLE_ANALYTICS_TRACKING_ID")
    ))
    analytics_script = """<script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('config', '%s');
        </script>""" % server.config.get("GOOGLE_ANALYTICS_TRACKING_ID")

app = dash.Dash(
    __name__,
    meta_tags=[
        {"charset": "UTF-8"},
        {"http-equiv": "X-UA-Compatible", "content": "IE=edge,chrome=1"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
    ],
    external_stylesheets=[
        "https://use.typekit.net/nri0jbb.css",
        "https://fonts.googleapis.com/icon?family=Material+Icons",
        "/static/css/sanitize.css",
        "/static/css/styles.css",
    ],
    external_scripts=scripts,
    server=server,
    url_base_pathname='/file/'
)
app.config.suppress_callback_exceptions = True

with server.app_context():
    footer = render_template('footer.html.j2')

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        {%config%}
        {%scripts%}
        ''' + analytics_script + '''
        ''' + footer + '''
    </body>
</html>
'''

app.title = '360Giving Insights'
