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
from charts import list_to_string, message_box

dash_resumable_upload.decorate_server(app.server, "uploads")


layout = html.Div(id="upload-container", className='w-two-thirds-l center', children=[
    html.Div(className="flex flex-wrap justify-center", children=[
        html.Div(id='output-data-upload', className='w-100'),
        html.Div(className='w-100 tc ph3 ph5-l pt3 pb4 white bg-threesixty-one', children=[
            html.H2('Upload a file', className='f3'),
            html.P(className='light-gray', children=[
                'File must meet the ',
                html.A(
                    children='360 Giving data standard',
                    href='https://www.threesixtygiving.org/support/standard/',
                    target='_blank',
                    className='light-gray underline dim'
                )
            ]),
            html.Div(className='field', children=[
                # html.Label(children='Select file'),
                dash_resumable_upload.Upload(
                    id='upload-data',
                    maxFiles=1,
                    maxFileSize=1024*1024*1000,  # 100 MB
                    filetypes=['csv', 'xlsx'],
                    service="/upload_resumable",
                    textLabel="Drop your file here to upload",
                    startButton=True
                ),
            ]),
        ]),
        html.Div(className='w-100 tc ph3 ph5-l pv3 f3 flex items-center justify-center', children='or'),
        html.Div(className='w-100 tc ph3 ph5-l pt3 pb4 white bg-threesixty-two', children=[
            html.H2(className='f3', children=[
                'Select file from ',
                html.A(
                    children='360 Giving registry of publishers',
                    href='http://data.threesixtygiving.org/',
                    target='_blank',
                    className='white underline dim'
                    )
            ]),
            dcc.Dropdown(id='registry-list', className='black tl', options=[]),
            html.Button('Fetch file', className='mt3 f6 link dim ph3 pv2 mb2 dib white bg-near-black', id='import-registry'),
        ]),
        # html.Div(className='w-third tc pa5 white bg-threesixty-three', children=[
        #     html.H2('View existing dashboards'),
        #     html.Ul(id="files-list", children=[])
        # ]),
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

    return message_box(
        'File fetch results',
        [
            html.Div(children=[
                html.Strong('File fetched: '),
                filename
            ]),
            (html.H6(datetime.datetime.fromtimestamp(date)) if date else ""),
            dcc.Link(href='/file/{}'.format(fileid),
                     className='link dim near-black bg-threesixty-three pv2 ph3 mv3 dib',
                     children='Data uploaded - view results >')
        ]
    )


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
    try:
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

    except Exception as e:
        return message_box("Could not load file", str(e), error=True)


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
