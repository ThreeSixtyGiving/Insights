# -*- coding: utf-8 -*-
import base64
import datetime
import io
import hashlib
import pickle
import json
import os

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import dash_resumable_upload

import pandas as pd
import redis

from charts import *
from prepare_data import prepare_data, fetch_geocodes

app = dash.Dash(__name__)
dash_resumable_upload.decorate_server(app.server, "uploads")
server = app.server

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
r = redis.StrictRedis.from_url(REDIS_URL)

# Append an externally hosted CSS stylesheet
app.css.append_css({
    "external_url": "https://cdn.jsdelivr.net/npm/semantic-ui@2.3.3/dist/semantic.min.css"
})

@app.server.route('/redis_cache')
def check_redis_cache():
    return json.dumps({"keys": {x.decode('utf8'): len(r.get(x)) for x in r.keys()}})

@app.server.route('/refresh_lookup_cache')
def refresh_lookup_cache():
    # prepare the cache
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

    html.Div(id="dashboard-container", className='ui grid', children=[
        html.Div(className="row", children=[

            html.Div(className="twelve wide column", children=[
                html.Div(id="dashboard-output", children=[], className='ui grid'),
            ]),

            html.Div(className="four wide column", children=[
                html.Form(id="dashboard-filter", className='ui form', children=[
                    html.Div(className='field', children=[
                        html.Label(children='Grant programme'),
                        dcc.Dropdown(
                            id='df-change-grant-programme',
                            options=[{'label': 'All grants', 'value': '__all'}],
                            multi=True,
                            value='__all'
                        ),
                    ]),

                    html.Div(className='field', children=[
                        html.Label(children='Data years'),
                        dcc.RangeSlider(
                            id='df-change-year',
                            min=2015,
                            max=2018,
                            step=1,
                            value=[2015,2018]
                        ),
                    ]),

                    html.Div(className='field', children=[
                        html.Label(children='Select file'),
                        dash_resumable_upload.Upload(
                            id='upload-data',
                            maxFiles=1,
                            maxFileSize=1024*1024*1000,  # 100 MB
                            filetypes=['csv', 'xlsx'],
                            service="/upload_resumable",
                            textLabel="Drag and Drop Here to upload!",
                            startButton=False
                        ),
                    ]),
                    
                    html.Div(children=dt.DataTable(rows=[{}], id="df-datatable"), style={"display": "none"}),

                    html.Div(id='output-data-upload'),
                    html.Div(id='output-data-id'),

                ])
            ])
        ])
    ]),
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
        # elif filename.endswith("pkl"):
        #     # Assume that the user uploaded an pickle file
        #     # @TODO: switch off in production - very unsafe
        #     df = pd.read_pickle(io.BytesIO(decoded))
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

def save_to_cache(fileid, df):
    r.set(fileid, pickle.dumps(df))
    app.server.logger.info("Dataframe [{}] saved to redis".format(fileid))


def get_from_cache(fileid):
    df = r.get(fileid)
    if df:
        app.server.logger.info("Retrieved dataframe [{}] from redis".format(fileid))
        return pickle.loads(df)

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
        # try:
        #     df = get_dataframe(filename, contents, date)
        # except Exception as e:
        #     print(e)
        #     print(traceback.format_exc())
        #     return html.Div([
        #         'There was an error processing this file.',
        #         e
        #     ])

        save_to_cache( fileid, df )

    return html.Div([
        html.H5(filename),
        (html.H6(datetime.datetime.fromtimestamp(date)) if date else ""),
        html.Hr(),  # horizontal line
    ])


@app.callback(Output('output-data-id', 'children'),
              [Input('upload-data', 'fileNames'),
               Input('url', 'pathname')])
def update_file_id(fileNames, pathname):
    if pathname is not None and pathname.startswith("/file/"):
        return pathname.replace("/file/", "")
    if fileNames is not None:
        return get_fileid(None, fileNames[-1], None)


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'fileNames')])
def update_output(fileNames):
    if fileNames is not None:
        children = [
            parse_contents(None, fileNames[-1], None)]
        return children


@app.callback(Output('df-change-grant-programme', 'options'),
              [Input('output-data-id', 'children')])
def grant_programme_dropdown(fileid):
    df = get_from_cache(fileid)
    if df is None:
        return []
    grant_programmes = df["Grant Programme:Title"].value_counts()
    return [{'label': '{} ({})'.format(i[0], i[1]), 'value': i[0]}
         for i in grant_programmes.iteritems()]


@app.callback(Output('df-change-year', 'min'),
              [Input('output-data-id', 'children')])
def year_select_min(fileid):
    df = get_from_cache(fileid)
    if df is None:
        return 2015
    return df["Award Date"].dt.year.min() - 1
    

@app.callback(Output('df-change-year', 'max'),
              [Input('output-data-id', 'children')])
def year_select_max(fileid):
    df = get_from_cache(fileid)
    if df is None:
        return 2015
    return df["Award Date"].dt.year.max() + 1
    

@app.callback(Output('df-change-year', 'marks'),
              [Input('output-data-id', 'children')])
def year_select_marks(fileid):
    df = get_from_cache(fileid)
    if df is None:
        return {2015: "2015", 2018: "2018"}
    min_max = range(df["Award Date"].dt.year.min() - 1, df["Award Date"].dt.year.max() + 1)
    return {str(i): str(i) for i in min_max}
    

@app.callback(Output('df-change-year', 'value'),
              [Input('output-data-id', 'children')])
def year_select_value(fileid):
    df = get_from_cache(fileid)
    if df is None:
        return [2015, 2018]
    return [df["Award Date"].dt.year.min() - 1, df["Award Date"].dt.year.max() + 1]
    

@app.callback(Output('dashboard-output', 'children'),
              [Input('df-change-grant-programme', 'value'),
               Input('df-change-year', 'value'),
               Input('output-data-id', 'children')])
def dashboard_output(grant_programme, year, fileid):
    df = get_filtered_df(fileid, grant_programme=grant_programme, year=year)
    if df is None:
        return []

    outputs = []
    

    outputs.append(
        html.Div(className='row', children=[
            html.Div(className='column', children=[
                html.H2(children=get_funder_output(df, grant_programme), id="funder-name")
            ])
        ])
    )
    outputs.append(
        html.Div(className='row', children=[
            html.Div(className='column', children=[get_statistics(df)])
        ])
    )

    charts = []

    charts.append(amount_awarded_chart(df))
    if "Grant Programme:Title" in df.columns:
        charts.append(grant_programme_chart(df))
    charts.append(awards_over_time_chart(df))
    charts.append(organisation_type_chart(df))
    charts.append(region_and_country_chart(df))
    charts.append(organisation_age_chart(df))
    charts.append(organisation_income_chart(df))

    row = []
    for i in charts:
        # if len(row)==2:
        #     outputs.append(html.Div(className='row', children=row))
        #     row = []
        row.append(html.Div(className='sixteen wide column', children=i))
    if row:
        outputs.append(html.Div(className='row', children=row))

        
    outputs.append(
        html.Div(className='row', children=[
            html.Div(className='column', children=[dataframe_datatable(df)])
        ])
    )

    return outputs


def get_filtered_df(fileid, **filters):
    df = get_from_cache(fileid)

    # Filter on grant programme
    if filters.get("grant_programme") and '__all' not in filters.get("grant_programme", []):
        df = df[df["Grant Programme:Title"].isin(filters.get("grant_programme", []))]

    # filter on year
    if filters.get("year") and df is not None:
        df = df[
            (df["Award Date"].dt.year >= filters.get("year")[0]) & 
            (df["Award Date"].dt.year <= filters.get("year")[1])
        ]

    return df

if __name__ == '__main__':
    app.run_server(debug=True)
