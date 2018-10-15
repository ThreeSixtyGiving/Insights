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

from app import app
from load_data import get_cache, get_from_cache, save_to_cache, get_registry, fetch_reg_file
from prepare_data import prepare_data, fetch_geocodes
from charts import list_to_string, message_box

dash_resumable_upload.decorate_server(app.server, "uploads")


layout = html.Div(id="upload-container", className='w-two-thirds-l center', children=[
    html.Div(className="flex flex-wrap justify-center", children=[
        html.Div(className='w-100 tc ph3 ph5-l pt3 pb4', children=[
            html.H2('Welcome', className='f3 ostrich threesixty-red'),
            html.P(className='', children=[
                'Discover grantmaking insights by uploading or selecting a file that meets the ',
                html.A(
                    children='360Giving standard',
                    href='https://www.threesixtygiving.org/support/standard/',
                    target='_blank',
                    className='underline dim'
                )
            ]),
            html.P(className='', children=[
                '''This 360Giving Insights tool will check the data for recipients 
                with charity or company numbers and combine extra data about them. 
                It will also add data based on the postcode of the recipients.''',
            ]),
        ]),
        html.Div(id='output-data-upload', className='w-100'),
        dcc.Interval(
            id='update-interval',
            interval=60*60*5000,  # in milliseconds
            n_intervals=0
        ),
        html.Div(className='w-100 tc ph3 ph5-l pt3 pb4 white bg-threesixty-red', children=[
            html.H2('Upload a file', className='f3 ostrich'),
            html.P(className='light-gray', children=[
                'File must meet the ',
                html.A(
                    children='360Giving data standard',
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
                    startButton=True,
                    # cancelButton=False,
                    # pauseButton=False,
                ),
            ]),
        ]),
        html.Div(className='w-100 tc ph3 ph5-l pv3 f3 flex items-center justify-center', children='or'),
        html.Div(className='w-100 tc ph3 ph5-l pt3 pb4 white bg-threesixty-orange', children=[
            html.H2(className='f3 ostrich', children=[
                'Select file from ',
                html.A(
                    children='360Giving registry of publishers',
                    href='http://data.threesixtygiving.org/',
                    target='_blank',
                    className='white underline dim'
                    )
            ]),
            dcc.Dropdown(id='registry-list', className='black tl', options=[]),
            html.Button('Fetch file', className='mt3 f6 link dim ph3 pv2 mb2 dib white bg-near-black', id='import-registry'),
        ]),
        # html.Div(className='w-third tc pa5 white bg-threesixty-yellow', children=[
        #     html.H2('View existing dashboards ostrich'),
        #     html.Ul(id="files-list", children=[])
        # ]),
    ])
])


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


@app.callback(Output('registry-list', 'options'),
              [Input('output-data-upload', 'children')])
def update_registry_list(_):
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

# =============================
# Callbacks for calling workers
#
# From: https://github.com/WileyIntelligentSolutions/wiley-boilerplate-dash-app/
# =============================


# this callback checks submits the query as a new job, returning job_id to the invisible div
@app.callback(Output('job-id', 'children'),
              [Input('upload-data', 'fileNames'),
               Input('import-registry', 'n_clicks')],
              [State('registry-list', 'value')])
def update_output(fileNames, n_clicks, regid):
    if (n_clicks is None or regid is None) and fileNames is None:
        return ''
    
    # a query was submitted, so queue it up and return job_id
    q = Queue(connection=get_cache())
    job_id = str(uuid.uuid4())
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
                job = q.enqueue_call(func=parse_contents,
                                     args=(contents, filename, None),
                                     timeout='15m',
                                     job_id=job_id)
                return json.dumps({"job": job_id})

        if fileNames is not None:
            job = q.enqueue_call(func=parse_contents,
                                 args=(None, fileNames[-1], None),
                                 timeout='15m',
                                 job_id=job_id)
            return json.dumps({"job": job_id})

    except Exception as e:
        return json.dumps({"error": str(e)})
        # message_box("Could not load file", str(e), error=True)


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
               Input('job-id', 'children')])
def update_results_tables(n_intervals, job_status):

    if job_status is None:
        return

    job_status = json.loads(job_status)
    job_id = job_status.get("job")

    # the job id may be an error - in which case return the error
    if "error" in job_status or job_id is None:
        return message_box("Error fetching file", job_status.get("error", "Unknown error"), error=True)

    job = get_queue_job(job_id)
    if job is None:
        return ''
    
    # check for failed jobs
    if job.is_failed:
        return message_box(
            'Error fetching file',
            [
                html.Div(children=[
                    html.Strong('Attempted to fetch file: '),
                    job.args[1]
                ]),
                (html.H6(datetime.datetime.fromtimestamp(
                    job.args[2])) if job.args[2] else ""),
                html.P('Could not fetch file'),
                html.Div(className='bg-light-gray pa1 f6 ws-pre pre', children=[
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
            return message_box(
                'Fetching file',
                [
                    html.P(html.Strong(job.meta["stages"][job.meta["progress"]["stage"]])),
                    html.P('Step {} of {}'.format(
                        job.meta["progress"]["stage"],
                        len(job.meta["stages"])
                    )),
                    html.Div(className='bg-moon-gray br-pill h1 overflow-y-hidden', children=[
                        html.Div(className='bg-threesixty-red br-pill h1 shadow-1',
                                 style={"width": step_width})
                    ])
                ] + progress
            )
        return message_box('Fetching file', [html.P(html.Strong("Starting to fetch file..."))])

    # results are ready
    fileid, filename, date = result
    return message_box(
        'File fetch results',
        [
            html.Div(children=[
                html.Strong('File fetched: '),
                filename
            ]),
            (html.H6(datetime.datetime.fromtimestamp(date)) if date else ""),
            dcc.Link(href='/file/{}'.format(fileid),
                    className='link dim near-black bg-threesixty-yellow pv2 ph3 mv3 dib',
                    children='Data uploaded - view results >')
        ]
    )


# this callback orders the table to be regularly refreshed if
# the user is waiting for results, or to be static (refreshed once
# per hour) if they are not.
@app.callback(Output('update-interval', 'interval'),
              [Input('job-id', 'children'),
              Input('update-interval', 'n_intervals')])
def stop_or_start_table_update(job_status, n_intervals):

    if job_status is None:
        return 60*60*1000

    job_status = json.loads(job_status)
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
