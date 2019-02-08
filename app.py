# -*- coding: utf-8 -*-
import dash

app = dash.Dash(
    __name__,
    meta_tags=[
        {"charset": "UTF-8"},
        {"http-equiv": "X-UA-Compatible", "content": "IE=edge,chrome=1"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
    ],
    external_stylesheets=[
        "https://use.typekit.net/nri0jbb.css",
        "https://fonts.googleapis.com/icon?family=Material+Icons"
    ]
)
app.config.suppress_callback_exceptions = True

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        {%config%}
        {%scripts%}
    </body>
</html>
'''
