import hashlib
import os
import json
import io
import uuid
import time

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_resumable_upload

import pandas as pd
from rq import Queue
import humanize

from app import app
from load_data import get_cache, get_from_cache, save_to_cache, get_registry, fetch_reg_file
from prepare_data import prepare_data, fetch_geocodes
from charts import list_to_string, format_currency

dash_resumable_upload.decorate_server(app.server, "uploads")


def upload_progress(title, contents, error=False):
    return html.Div(
        className='homepage__data-selection js-homepage-dataset-selection-window',
        children=[
            html.Div(className='homepage__data-selection__window', children=[
                html.Div(className='homepage__data-selection__highlight', children=[title]),
                html.Ul(className='homepage__data-selection__sets', children=contents),
            ]),
        ]
    )


def dataset_selection():
    return html.Div(
        className='homepage__data-selection hidden js-homepage-dataset-selection-window',
        id='file-selection-modal',
        children=[
            html.Div(className='homepage__data-selection__window', children=[
                html.Div(className='homepage__data-selection__highlight', children=[
                    "Datasets",
                    html.Div(
                        className='close-button js-homepage-dataset-selection-window-close',
                        id='file-selection-close'
                    ),
                ]),
                html.Ul(className='homepage__data-selection__sets',
                        id='registry-list', children=[]),
            ]),
        ]
    )


def dataset_upload():
    return html.Div(
        className='homepage__data-selection hidden js-homepage-dataset-upload-window',
        id='upload-dataset-modal',
        children=[
            html.Div(className='homepage__data-selection__window', children=[
                html.Div(className='homepage__data-selection__highlight', children=[
                    "Upload Data",
                    html.Div(
                        className='close-button js-homepage-dataset-upload-window-close',
                        id='upload-dataset-close'
                    ),
                ]),
                dash_resumable_upload.Upload(
                    id='upload-data',
                    maxFiles=1,
                    maxFileSize=1024*1024*1000,  # 100 MB
                    filetypes=['csv', 'xlsx'],
                    service="/upload_resumable",
                    textLabel="Drop your file here to upload",
                    startButton=True,
                    # cancelButton=False,
                    # pauseButton=False,
                    className='homepage__data-selection__upload-drop highlight',
                    children=[
                            html.P([
                                html.Span(style={
                                        "color": "#9c1f61", "fontWeight": "400"}, children="Data Privacy Information:"),
                                """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut
                                labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
                                nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit
                                esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
                                in culpa qui officia deserunt mollit anim id est laborum."""
                            ])
                    ]
                ),
                html.Div(className="homepage__data-selection__upload-wrapper", children=[
                    html.Button(className="homepage__data-selection__upload-button js-dataset-upload", children=[
                        "Upload file"
                    ])
                ]),
            ]),
        ]
    )


def homepage_header():
    return html.Div(className="homepage__header", children=[
        html.Img(src=app.get_asset_url("images/360-insights-logo.png")),
        html.Br(),
        html.H2("Discover"),
        html.H1("Grantmaking Insights"),
        html.P("""The 360Giving Insights tool will check the data for recipients with 
                charity or company numbers and combine extra data about them, like information 
                based on the recipients’ postcode.""")
    ])


def homepage_file_selection():
    return html.Div(className='homepage__file-selection', children=[
        html.Div(className='homepage__file-selection__wrapper', children=[
            html.P([
                "Select one of our datasets",
                html.Br(),
                "or upload a file that meets the 360Giving Standard."
            ]),
            html.Div(className='homepage__file-selection__zone', children=[
                html.Button(
                    className='js-choose-dataset-btn button',
                    id='file-selection-open',
                    children=[
                        "Choose a dataset"
                    ]
                ),
                html.Div(
                    className='homepage__file-selection__upload js-upload-dataset-btn',
                    id='upload-dataset-open',
                    children=[
                        html.P(className='text', children='Upload a file'),
                        html.P(
                            className='homepage__file-selection__upload-icon', children='cloud_upload'),
                    ]
                ),
            ])
        ])
    ])

def homepage_data_sources():
    return html.Div(className='homepage__data-sources', children=[
        html.Div(style={'display': 'inline-block', 'textAlign': 'left'}, children=[
            html.H2("Data sources"),
            dcc.Markdown("""
Charity data is sourced from [findthatcharity.uk](https://findthatcharity.uk) and postcode
data from [postcodes.findthatcharity.uk](https://postcodes.findthatcharity.uk). 
Company data is fetched using Companies House URIs. All external data is used under 
the [Open Government Licence](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
                """)
        ]),
    ])


def homepage_newsletter(): 
    return html.Div(className='homepage__newsletter', children=[
        html.Div(className='wrapper', children=[
            html.Form(className='homepage__newsletter__form', children=[
                dcc.Input(type='email',
                        name='email',
                        placeholder='Signup for our Newsletter...'),
                dcc.Input(type="submit", value='send')
            ])
        ]),
    ])

def footer():
    return html.Footer([
        html.Ul(className='footer__social', children=[
                html.Li(html.A(href='https://github.com/ThreeSixtyGiving/',
                               children=html.Img(src='/images/icon-github.png', title='Github'))),
                html.Li(html.A(href='https://twitter.com/360giving',
                               children=html.Img(src='/images/icon-twitter.png', title='Twitter'))),
                ]),
        html.Div(className="flex-wrapper", children=[
            html.Section([
                html.Div([
                    "MORE",
                    html.Br(),
                    "INFORMATION",
                    html.Ul(className='footer__navigation', children=[
                            html.Li(html.A(href='#', children='Contact')),
                            html.Li(html.A(href='#', children='Support')),
                            html.Li(html.A(href='#', children='Tools')),
                            ])
                ]),
            ]),
            html.Section([
                html.Ul(className='footer__navigation', children=[
                        html.Li(html.A(href='#', children='Privacy Notice')),
                        html.Li(html.A(href='#', children='Terms & Conditions')),
                        html.Li(html.A(href='#', children='License')),
                        ])
            ]),
            html.Section([
                html.P(style={"fontWeight": "300"}, children=[
                    html.Img(src='/images/360footer.png'),
                    html.Br(),
                    "A quick line of text about 360Giving."
                ]),
            ]),
        ]),
        html.Div(className="footer__divider", children=[
            html.Hr(),
            html.Div(className='footer__divider__columns', children=[
                html.P("Cookie Policy | Take Down Policy"),
                html.P(style={'textAlign': 'right'}, children=[
                    "360Giving is a company limited by guarantee 09668396 and a registered charity 1164883.",
                ]),
            ]),
        ]),
    ])

def homepage():

    return [
        html.Div(
            id='output-data-upload',
            children=[]
        ),
        dataset_selection(),
        dataset_upload(),
        dcc.Interval(
            id='update-interval',
            interval=60*60*5000,  # in milliseconds
            n_intervals=0
        ),
        homepage_header(),
        homepage_file_selection(),
        homepage_data_sources(),
        homepage_newsletter(),
        footer(),
    ]


def get_dataframe(filename, contents=None, date_=None, fileid=None):
    df = None
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

    return (fileid, filename, date)


def get_existing_files():
    r = get_cache()
    return {
        k.decode('utf8'): json.loads(v.decode('utf8')) for k, v in r.hgetall("files").items()
    }


@app.callback(Output('files-list', 'children'),
              [Input('output-data-upload', 'children')])
def update_files_list(_):
    return [
        html.Li([
            dcc.Link(href='/file/{}'.format(k), children=list_to_string(v["funders"]))
        ]) for k, v in get_existing_files().items()
    ]

@app.callback(Output('registry-list', 'children'),
              [Input('output-data-upload', 'children')])
def update_registry_list(_):
    reg = get_registry()
    publishers = {}
    for v in reg:
        publisher = v.get("publisher", {}).get("name", "")
        grant_count = v.get("datagetter_aggregates", {}).get("count", 0)
        grant_amount = v.get("datagetter_aggregates", {}).get("currencies", {}).get("GBP", {}).get("total_amount", None)
        if grant_amount:
            grant_amount = format_currency(grant_amount, abbreviate=True)
            grant_amount = "{}{}".format(*grant_amount)

        min_award_date = pd.to_datetime(v.get("datagetter_aggregates", {}).get("min_award_date", None))
        max_award_date = pd.to_datetime(v.get("datagetter_aggregates", {}).get("max_award_date", None))

        min_award_date = min_award_date.strftime("%b '%y") if not pd.isna(min_award_date) else None
        max_award_date = max_award_date.strftime("%b '%y") if not pd.isna(max_award_date) else None

        if min_award_date == max_award_date:
            award_date_str = min_award_date
        else:
            award_date_str = "{} - {}".format(min_award_date, max_award_date)

        if publisher not in publishers:
            publishers[publisher] = []
        publishers[publisher].append(html.Li(
            className='homepage__data-selection__data-list__item',
            children=dcc.Link(
                href='/registry/{}'.format(v.get('identifier')),
                children=html.Ul([
                    html.Li(
                        className='homepage__data-selection__data-list__item__data-fixed',
                        children=v.get("title", "")
                    ),
                    html.Li(
                        className='homepage__data-selection__data-list__item__data-notfixed',
                        children="{:,.0f} records".format(grant_count)
                    ),
                    html.Li(
                        className='homepage__data-selection__data-list__item__data-notfixed',
                        children=award_date_str
                    ),
                    html.Li(
                        className='homepage__data-selection__data-list__item__data-notfixed',
                        children=grant_amount
                    ),
                ])
            )
        ))
    
    return [html.Li(className='homepage__data-selection__set', children=[
        html.H4(className='homepage__data-selection__set-name', children=publisher),
        html.Ul(className='homepage__data-selection__data-list', children=files),
    ]) for publisher, files in publishers.items()]

# =============================
# Callbacks for calling workers
#
# From: https://github.com/WileyIntelligentSolutions/wiley-boilerplate-dash-app/
# =============================


@app.callback(Output('fetch-registry-id', 'data'),
              [Input('url', 'pathname')])
def fetch_registry_id(pathname):
    if pathname is not None and pathname.startswith("/registry/"):
        return pathname.replace("/registry/", "")


@app.callback(Output('job-task', 'data'),
              [Input('upload-data', 'fileNames'),
               Input('fetch-registry-id', 'data')])
def set_job_task(fileNames, regid):
    return {
        "fileNames": fileNames,
        "regid": regid
    }

# this callback checks submits the query as a new job, returning job_id to the invisible div
@app.callback(Output('job-id', 'data'),
              [Input('job-task', 'data')])
def update_output(job_task):
    print(job_task)
    if not job_task:
        return None

    regid = job_task.get("regid")
    fileNames = job_task.get("fileNames")
    
    # a query was submitted, so queue it up and return job_id
    q = Queue(connection=get_cache())
    job_id = str(uuid.uuid4())
    try:
        if regid is not None:
            reg = get_registry()
            regentry = [x for x in reg if x["identifier"]==regid]
            if len(regentry)==1:
                regentry = regentry[0]
                url = regentry.get("distribution", [{}])[0].get("downloadURL")
                filetype = regentry.get("datagetter_metadata", {}).get("file_type")
                contents = fetch_reg_file(url)
                filename = url if url.endswith(filetype) else "{}.{}".format(url, filetype)
                job = q.enqueue_call(func=parse_contents,
                                     args=(contents, filename, None),
                                     timeout='15m',
                                     job_id=job_id)
                return {"job": job_id}

        if fileNames is not None:
            job = q.enqueue_call(func=parse_contents,
                                 args=(None, fileNames[-1], None),
                                 timeout='15m',
                                 job_id=job_id)
            return {"job": job_id}

    except Exception as e:
        return {"error": str(e)}


def get_queue_job(job_id):
    if not isinstance(job_id, str):
        return None
    q = Queue(connection=get_cache())
    failed_q = Queue('failed', connection=get_cache())
    failed_job = failed_q.fetch_job(job_id)
    if failed_job:
        return failed_job
    return q.fetch_job(job_id)


# this callback checks if the job result is ready.  If it's ready
# the results return to the table.  If it's not ready, it pauses
# for a short moment, then empty results are returned.  If there is
# no job, then empty results are returned.
@app.callback(Output('output-data-upload', 'children'),
              [Input('update-interval', 'n_intervals'),
               Input('job-id', 'data')])
def update_results_tables(n_intervals, job_status):

    if job_status is None:
        return

    job_id = job_status.get("job")

    # the job id may be an error - in which case return the error
    if "error" in job_status or job_id is None:
        return upload_progress("Error fetching file", job_status.get("error", "Unknown error"), error=True)

    job = get_queue_job(job_id)
    if job is None:
        return ''
    
    # check for failed jobs
    if job.is_failed:
        return upload_progress(
            'Error fetching file',
            [
                html.Div(children=[
                    html.Strong('Attempted to fetch file: '),
                    job.args[1]
                ]),
                (html.H6(datetime.datetime.fromtimestamp(
                    job.args[2])) if job.args[2] else ""),
                html.P('Could not fetch file'),
                html.Div(className='', children=[
                    html.Pre(job.exc_info),
                ]),
            ],
            error=True
        )

    # job exists - try to get result
    result = job.result
    if result is None:
        # results aren't ready, show progres
        if "progress" in job.meta:
            progress = []
            if job.meta["progress"].get("progress"):
                width = '{0:.1f}%'.format(
                    (job.meta["progress"].get("progress")[0] / job.meta["progress"].get("progress")[1]) * 100
                )
                progress = [
                    html.P('Processed {} of {}'.format(
                        job.meta["progress"].get("progress")[0],
                        job.meta["progress"].get("progress")[1]
                    )),
                    html.Div(className='bg-moon-gray br-pill h1 overflow-y-hidden', children=[
                        html.Div(className='bg-threesixty-orange br-pill h1 shadow-1', style={"width": width})
                    ])
                ]
            step_width = '{0:.1f}%'.format(
                (job.meta["progress"]["stage"] /
                 len(job.meta["stages"])) * 100
            )
            return upload_progress(
                'Fetching file',
                [
                    html.P(html.Strong(job.meta["stages"][job.meta["progress"]["stage"]])),
                    html.P('Step {} of {}'.format(
                        job.meta["progress"]["stage"],
                        len(job.meta["stages"])
                    )),
                    # @TODO: progress bar
                    html.Div(className='', children=[
                        html.Div(className='',
                                 style={"width": step_width})
                    ])
                ] + progress
            )
        return upload_progress('Fetching file', [html.P(html.Strong("Starting to fetch file..."))])

    # results are ready
    fileid, filename, date = result
    return upload_progress(
        'File fetch results',
        [
            html.Div(children=[
                html.Strong('File fetched: '),
                filename
            ]),
            (html.H6(datetime.datetime.fromtimestamp(date)) if date else ""),
            dcc.Link(href='/file/{}'.format(fileid),
                    className='',
                    children='Data uploaded - view results >')
        ]
    )


# this callback orders the table to be regularly refreshed if
# the user is waiting for results, or to be static (refreshed once
# per hour) if they are not.
@app.callback(Output('update-interval', 'interval'),
              [Input('job-id', 'data'),
              Input('update-interval', 'n_intervals')])
def stop_or_start_table_update(job_status, n_intervals):

    if job_status is None:
        return 60*60*1000
        
    job_id = job_status.get("job")
    job = get_queue_job(job_id)

    if job is None:
        # the job does not exist, therefore stop regular refreshing
        return 60*60*1000
        
    if job.is_failed:
        # the job has failed, therefore semi-regular refreshing
        return 10*1000

    # the job exists - try to get results
    if job.result:
        # the results are ready, therefore stop regular refreshing
        return 60*60*1000

    # a job is in progress but we're waiting for results
    # therefore regular refreshing is required.  You will
    # need to fine tune this interval depending on your
    # environment.
    return 1000
