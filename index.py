import json
import os
import io

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table_experiments as dt
import dash_resumable_upload
import flask
import pandas as pd

from app import app
from apps import data_display, file_load, status
from load_data import get_cache, get_filtered_df
from prepare_data import fetch_geocodes

server = app.server

@server.route('/redis_cache')
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

@server.route('/refresh_lookup_cache')
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


@server.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(server.root_path, 'assets'),
                                     'favicon.ico')

@server.route('/images/<path:path>')
def send_images(path):
    return flask.send_from_directory('assets/images', path)

@server.route('/file/<fileid>.<format>')
def download_file(fileid, format):
    df = get_filtered_df(fileid)
    if df is not None:
        if format=="csv":
            csvdata = df.to_csv(index=False)
            return flask.Response(
                csvdata,
                mimetype="text/csv",
                headers={"Content-disposition":
                        "attachment; filename={}.csv".format(fileid)})
        elif format == 'xlsx':
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            csvdata = df.to_excel(writer, sheet_name='grants', index=False)
            writer.save()
            return flask.Response(
                output.getvalue(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-disposition":
                         "attachment; filename={}.xlsx".format(fileid)})
        elif format=="json":
            pass
        flask.abort(400)
    flask.abort(404)
    
app.title = '360Giving Insights'
app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', className='cf'),
    dcc.Store(id='fetch-registry-id'),
    dcc.Store(id='output-data-id'),
    dcc.Store(id='job-task'),
    dcc.Store(id='job-id'),
    html.Div(dt.DataTable(rows=[{}]), style={'display': 'none'}), # make sure we can load dash_table_experiments
    html.Div(dash_resumable_upload.Upload(), style={'display': 'none'}), # dummy upload to make sure dash loads dash_resumable_upload
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None or pathname == '/':
        return file_load.homepage()
    elif pathname.startswith('/registry/'):
        return file_load.homepage()
    elif pathname.startswith('/file/'):
        return data_display.layout
    elif pathname == '/status':
        return status.layout
    else:
        return '404'

# @TODO: move to utils
def add_class(className, existing_class):
    existing_class = existing_class.split(" ")
    if className not in existing_class:
        existing_class.append(className)
    return " ".join(existing_class)


def remove_class(className, existing_class):
    existing_class = existing_class.split(" ")
    if className in existing_class:
        existing_class.remove(className)
    return " ".join(existing_class)


@app.callback(Output('file-selection-modal', 'className'),
              [Input('file-selection-open', 'n_clicks_timestamp'), 
               Input('file-selection-close', 'n_clicks_timestamp')],
              [State('file-selection-modal', 'className')])
def toggle_dataset_selection_modal(file_selection_open, file_selection_close, existing_class):
    if (file_selection_open or 0) > (file_selection_close or 0):
        return remove_class('hidden', existing_class)
    else:
        return add_class('hidden', existing_class)

@app.callback(Output('upload-dataset-modal', 'className'),
              [Input('upload-dataset-open', 'n_clicks_timestamp'),
               Input('upload-dataset-close', 'n_clicks_timestamp')],
              [State('upload-dataset-modal', 'className')])
def toggle_upload_dataset_modal(upload_dataset_open, upload_dataset_close, existing_class):
    if (upload_dataset_open or 0) > (upload_dataset_close or 0):
        return remove_class('hidden', existing_class)
    else:
        return add_class('hidden', existing_class)


@app.callback(Output('output-data-id', 'data'),
              [Input('page-content', 'children')],
              [State('url', 'pathname')])
def update_file_id(_, pathname):
    if pathname is not None and pathname.startswith("/file/"):
        return pathname.replace("/file/", "")

if __name__ == '__main__':
    app.run_server(debug=True)
