import hashlib
import os
import json
import io

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_resumable_upload

import pandas as pd

from app import app
from load_data import get_cache, get_from_cache, save_to_cache, get_registry, fetch_reg_file
from prepare_data import prepare_data, fetch_geocodes
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
                html.H2('Select file from registry'),
                dcc.Dropdown(id='registry-list', options=[]),
                html.Button('Fetch file', id='import-registry'),
            ]),
            html.Div(className='row', children=[
                html.H2('View existing dashboards'),
                html.Ul(id="files-list", children=[])
            ]),
        ])
    ])
])


def get_dataframe(filename, contents=None, date_=None, fileid=None):
    if contents:
        if isinstance(contents, str):
            # if it's a string we assume it's dataurl/base64 encoded
            content_type, content_string = contents.split(',')
            contents = base64.b64decode(content_string)

        if filename.endswith("csv"):
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(contents.decode('utf-8')))
        elif filename.endswith("xls") or filename.endswith("xlsx"):
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(contents))
            
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
              [Input('upload-data', 'fileNames'),
               Input('import-registry', 'n_clicks')],
              [State('registry-list', 'value')])
def update_output(fileNames, n_clicks, regid):
    print("update_output", fileNames, n_clicks, regid)
    if n_clicks is not None and regid is not None:
        reg = get_registry()
        regentry = [x for x in reg if x["identifier"]==regid]
        if len(regentry)==1:
            regentry = regentry[0]
            url = regentry.get("distribution", [{}])[0].get("downloadURL")
            filetype = regentry.get("datagetter_metadata", {}).get("file_type")
            contents = fetch_reg_file(url)
            filename = url if url.endswith(filetype) else "{}.{}".format(url, filetype)
            return parse_contents(contents, filename, None)

    if fileNames is not None:
        return parse_contents(None, fileNames[-1], None)


@app.callback(Output('files-list', 'children'),
              [Input('output-data-upload', 'children')])
def update_files_list(_):
    print("update_files_list", _)
    return [
        html.Li([
            dcc.Link(href='/file/{}'.format(k), children=list_to_string(v["funders"]))
        ]) for k, v in get_existing_files().items()
    ]


@app.callback(Output('registry-list', 'options'),
              [Input('output-data-upload', 'children')])
def update_registry_list(_):
    print("update_registry_list", _)
    reg = get_registry()
    return [
        {
            'label': '{} ({}) [{:,.0f} grants]'.format(
                v.get("publisher", {}).get("name", ""), 
                v.get("title", ""),
                v.get("datagetter_aggregates", {}).get("count", 0)
            ),
            'value': v.get('identifier')
        } for v in reg if v.get("datagetter_metadata", {}).get("file_type") in ["xlsx", "csv"]
    ]
