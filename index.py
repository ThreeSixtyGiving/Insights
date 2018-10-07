import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table_experiments as dt
import dash_resumable_upload

from app import app
from apps import data_display, file_load, status
from load_data import get_cache
from prepare_data import fetch_geocodes

server = app.server

# Append an externally hosted CSS stylesheet
app.css.append_css({
    "external_url": "https://unpkg.com/tachyons@4.10.0/css/tachyons.min.css"
})
app.css.append_css({
    "external_url": "https://fonts.googleapis.com/css?family=Source+Sans+Pro"
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
    
app.title = '360 Giving Data Explorer'
app.layout = html.Div(className='pv2 ph4', children=[
    dcc.Location(id='url', refresh=False),
    html.Div(id="page-header", className='cf mv3 pv3 bb b-threesixty-two bw4', children=[
        html.A(
            className='fr mw4 mw5-ns mr3', 
            href='https://www.threesixtygiving.org/',
            target='_blank',
            children=[
            html.Img(className='',
                     src='https://www.threesixtygiving.org/wp-content/themes/360giving/assets/img/logo.png'),
        ]),
        html.H1(className='', children=[
            dcc.Link(href='/', className='link dim black',
                     children='360 Giving data explorer')
        ]),
    ]),
    html.Div(id='page-content', className='cf'),
    html.Div(id='output-data-id', className='f6 grey'),
    html.Div(dt.DataTable(rows=[{}]), style={'display': 'none'}), # make sure we can load dash_table_experiments
    html.Div(dash_resumable_upload.Upload(), style={'display': 'none'}), # dummy upload to make sure dash loads dash_resumable_upload
    html.Div(id="page-footer", className='cf mv3 pv3 bt b-threesixty-one bw4', children=[
        dcc.Markdown(className='fl w-100 w-third-l pr3', children='''
#### About the explorer

This tool showcases the potential of data published to the [360 giving standard](https://www.threesixtygiving.org/support/standard/). 
Upload a file that meets the 360 giving standard and the tool will display some key views of the data. 

When a file is uploaded the tool will check for any recipients with charity or company numbers and
download extra data about them, as well as adding data based on the postcode of the recipients.
        '''),
        dcc.Markdown(className='fl w-100 w-third-l ph3', children='''
#### Data protection and privacy

Any data you upload will be available at the URL created to anyone with the link. You should ensure that 
no confidential information is present in the data you upload, and that you have the appropriate 
permissions and licencing to upload the data. 

#### Data sources

Charity data is sourced from [findthatcharity.uk](https://findthatcharity.uk/about#data-sources) and postcode
data from [postcodes.findthatcharity.uk](https://postcodes.findthatcharity.uk/). Company data is fetched using
[Companies House URIs](https://www.gov.uk/government/organisations/companies-house/about-our-services#uri-info). 
All external data is used under the [Open Government Licence](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
        '''),
        dcc.Markdown(className='fl w-100 w-third-l pl3 tr', children='''
[Github](https://github.com/ThreeSixtyGiving/threethings) |
[360 Giving](https://www.threesixtygiving.org/)

Built by [David Kane](https://drkane.co.uk/) using 
[Dash by Plotly](https://dash.plot.ly/)
        ''')
    ]),
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None or pathname == '/':
        return file_load.layout
    elif pathname.startswith('/file/'):
        return data_display.layout
    elif pathname == '/status':
        return status.layout
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
