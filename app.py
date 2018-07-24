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

import pandas as pd
import redis

from charts import *
from prepare_data import prepare_data, fetch_geocodes

app = dash.Dash(__name__)
server = app.server

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
r = redis.StrictRedis.from_url(REDIS_URL)

# Append an externally hosted CSS stylesheet
app.css.append_css({
    "external_url": "https://cdn.jsdelivr.net/npm/semantic-ui@2.3.3/dist/semantic.min.css"
})

app.layout = html.Div(className='ui container', children=[
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
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select Files')
                            ]),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                            # Allow multiple files to be uploaded
                            multiple=True
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

def get_dataframe(contents, filename, date):
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
    if "geocodes" not in cache:
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
        df = get_dataframe(contents, filename, date)
        # try:
        #     df = get_dataframe(contents, filename, date)
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
        html.H6(datetime.datetime.fromtimestamp(date)),
        html.Hr(),  # horizontal line
        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename'),
               Input('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

@app.callback(Output('output-data-id', 'children'),
              [Input('upload-data', 'contents'),
               Input('upload-data', 'filename'),
               Input('upload-data', 'last_modified')])
def update_file_id(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            get_fileid(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children[0]


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
