import hashlib
import os
import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_resumable_upload

import pandas as pd

from app import app
from load_data import get_cache, get_from_cache, save_to_cache
from prepare_data import prepare_data
from charts import list_to_string

dash_resumable_upload.decorate_server(app.server, "uploads")


layout = html.Div(id="upload-container", className='ui grid', children=[
    html.Div(className="row", children=[
        html.Div(className="twelve wide column", children=[
            html.Div(className='row', children=[
                html.H2('Select your data'),
                html.Div(className='field', children=[
                    html.Label(children='Select file'),
                    dash_resumable_upload.Upload(
                        id='upload-data',
                        maxFiles=1,
                        maxFileSize=1024*1024*1000,  # 100 MB
                        filetypes=['csv', 'xlsx'],
                        service="/upload_resumable",
                        textLabel="Drag and Drop Here to upload!",
                        startButton=True
                    ),
                ]),
                html.Div(className='row', children=[
                    html.Div(id='output-data-upload')
                ]),
            ]),
            html.Div(className='row', children=[
                html.H2('Use existing uploads'),
                html.Ul(id="files-list", children=[])
            ]),
        ])
    ])
])


def get_dataframe(filename, contents=None, date_=None):
    if contents:
        content_type, content_string = contents.split(',')

        decoded = base64.b64decode(content_string)
        if filename.endswith("csv"):
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith("xls") or filename.endswith("xlsx"):
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            
    elif os.path.exists(os.path.join("uploads", filename)):
        if filename.endswith("csv"):
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(os.path.join("uploads", filename))
        elif filename.endswith("xls") or filename.endswith("xlsx"):
            # Assume that the user uploaded an excel file
            df = pd.read_excel(os.path.join("uploads", filename))

    if df is None:
        raise ValueError("No dataframe loaded")

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
    if "geocodes" not in cache or len(cache["geocodes"])==0:
        cache["geocodes"] = fetch_geocodes()

    # prepare the data
    df, cache = prepare_data(df, cache)

    r.set("lookup_cache", json.dumps(cache))

    return df

def get_fileid(contents, filename, date):
    hash_str = str(contents) + str(filename) + str(date)
    hash_obj = hashlib.md5(hash_str.encode())
    return hash_obj.hexdigest()

# https://dash.plot.ly/dash-core-components/upload
def parse_contents(contents, filename, date):
    fileid = get_fileid(contents, filename, date)
    df = get_from_cache(fileid)
    if df is None:
        df = get_dataframe(filename, contents, date)
        save_to_cache( fileid, df )

    return html.Div([
        html.H5(filename),
        (html.H6(datetime.datetime.fromtimestamp(date)) if date else ""),
        html.Hr(),  # horizontal line
        dcc.Link(href='/file/{}'.format(fileid), children='Data uploaded - view results')
    ])


def get_existing_files():
    r = get_cache()
    return {
        k.decode('utf8'): json.loads(v.decode('utf8')) for k, v in r.hgetall("files").items()
    }


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'fileNames')])
def update_output(fileNames):
    print("update_output", fileNames)
    if fileNames is not None:
        children = [
            parse_contents(None, fileNames[-1], None)]
        return children


@app.callback(Output('files-list', 'children'),
              [Input('output-data-upload', 'children')])
def update_files_list(_):
    print("update_files_list", _)
    return [
        html.Li([
            dcc.Link(href='/file/{}'.format(k), children=list_to_string(v["funders"]))
        ]) for k, v in get_existing_files().items()
    ]
