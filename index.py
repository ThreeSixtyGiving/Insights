import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table_experiments as dt
import dash_resumable_upload

from app import app
from apps import data_display, file_load
from load_data import get_cache


# Append an externally hosted CSS stylesheet
app.css.append_css({
    "external_url": "https://cdn.jsdelivr.net/npm/semantic-ui@2.3.3/dist/semantic.min.css"
})

@app.server.route('/redis_cache')
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

@app.server.route('/refresh_lookup_cache')
def refresh_lookup_cache():
    # prepare the cache
    r = get_cache()
    cache = r.get("lookup_cache")

    if cache is None:
        cache = {
            "charity": {},
            "company": {},
            "postcode": {},
            "geocodes": {}
        }
    else:
        cache = json.loads(cache.decode("utf8"))
    
    cache["geocodes"] = fetch_geocodes()

    r.set("lookup_cache", json.dumps(cache))
    return json.dumps(cache["geocodes"])
    

app.layout = html.Div(className='ui container', children=[
    dcc.Location(id='url', refresh=False),
    html.H1(children='360 Giving data explorer', className='ui dividing header'),
    html.Div(id='page-content'),
    html.Div(id='output-data-id'),
    html.Div(dt.DataTable(rows=[{}]), style={'display': 'none'}), # make sure we can load dash_table_experiments
    html.Div(dash_resumable_upload.Upload(), style={'display': 'none'}), # dummy upload to make sure dash loads dash_resumable_upload
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None or pathname == '/':
         return file_load.layout
    elif pathname.startswith('/file/'):
         return data_display.layout
    else:
        return '404'
    

@app.callback(Output('output-data-id', 'children'),
              [Input('page-content', 'children')],
              [State('url', 'pathname')])
def update_file_id(_, pathname):
    if pathname is not None and pathname.startswith("/file/"):
        return pathname.replace("/file/", "")

if __name__ == '__main__':
    app.run_server(debug=True)