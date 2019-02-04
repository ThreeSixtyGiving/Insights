# -*- coding: utf-8 -*-
import dash

app = dash.Dash(
    __name__,
    meta_tags=[
        {"charset": "UTF-8"},
        {"http-equiv": "X-UA-Compatible", "content": "IE=edge,chrome=1"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
    ],
    external_scripts=[
        {
            'src': "https://cdnjs.cloudflare.com/ajax/libs/jquery/2.1.4/jquery.min.js",
            'integrity': "sha256-ImQvICV38LovIsvla2zykaCTdEh1Z801Y+DSop91wMU=",
            'crossorigin': "anonymous"
        }, {
            'src': "https://cdnjs.cloudflare.com/ajax/libs/is-in-viewport/3.0.4/isInViewport.min.js",
            'integrity': "sha256-YCKf7pbD5WuWira7Ir49rglmeklV67h8HCeC7GCYWEw=",
            'crossorigin': "anonymous"
        }
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
