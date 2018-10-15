import json
import os

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table_experiments as dt
import dash_resumable_upload
import flask

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
    "external_url": "https://fonts.googleapis.com/css?family=Source+Sans+Pro%3A400%2C400i%2C600%2C700&ver=4.9.8"
})

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

    
app.title = '360Giving Insights'
app.layout = html.Div(children=[
    html.Div(className='pv2 ph4', children=[
        dcc.Location(id='url', refresh=False),
        html.Div(id="page-header", className='cf mv3 pv3', children=[
            html.H1(className='ostrich', children=[
                dcc.Link(href='/', className='link threesixty-red', children=[
                    html.Img(className='mw4point5',
                             src='https://www.threesixtygiving.org/wp-content/themes/360giving/assets/img/logo.png'),
                    'Insights',
                    html.Span(className='gray f4', children=' Beta')
                ]),
            ]),
        ]),
        html.Div(id='page-content', className='cf'),
        html.Div(id='output-data-id', className='f6 grey', style={'display': 'none'}),
        html.Div(id='job-id', style={'display': 'none'}), # invisible div to safely store the current job-id
        html.Div(dt.DataTable(rows=[{}]), style={'display': 'none'}), # make sure we can load dash_table_experiments
        html.Div(dash_resumable_upload.Upload(), style={'display': 'none'}), # dummy upload to make sure dash loads dash_resumable_upload
        html.Div(id="page-footer", className='cf mv3 pv3 bt b--threesixty-red bw4 flex flex-wrap', children=[
            dcc.Markdown(className='fl w-100 w-third-l pr3-l markdown', children='''
## About the explorer

This tool showcases the potential of data published to the [360 giving standard](https://www.threesixtygiving.org/support/standard/). 
Upload a file that meets the 360 giving standard and the tool will display some key views of the data. 

When a file is uploaded the tool will check for any recipients with charity or company numbers and
download extra data about them, as well as adding data based on the postcode of the recipients.
            '''),
            dcc.Markdown(className='fl w-100 w-third-l ph3-l markdown', children='''
## Data protection and privacy

Any data you upload will be available at the URL created to anyone with the link. You should ensure that 
no confidential information is present in the data you upload, and that you have the appropriate 
permissions and licencing to upload the data. 

## Data sources

Charity data is sourced from [findthatcharity.uk](https://findthatcharity.uk/about#data-sources) and postcode
data from [postcodes.findthatcharity.uk](https://postcodes.findthatcharity.uk/). Company data is fetched using
[Companies House URIs](https://www.gov.uk/government/organisations/companies-house/about-our-services#uri-info). 
All external data is used under the [Open Government Licence](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
            '''),
            dcc.Markdown(className='fl w-100 w-third-l ph3-l ph4 pb4 bg-threesixty-blue white markdown', children='''
## Feedback

360Giving Insights is in Beta. We would love your feedback on 
what works well and less well.

Please email us: 
**[labs@threesixtygiving.org](mailto:labs@threesixtygiving.org)**
            '''),
        ]),
    ]),
    html.Footer(className='pa3 bg-threesixty-grey cf', children=[
        html.A(className='link fl', href='http://www.threesixtygiving.org/', children=[
            html.Img(className='mw4', src='http://www.threesixtygiving.org/wp-content/themes/360giving/assets/img/logo-white.png'),
        ]),
        html.Nav(className='fr', children=[
            html.Ul(className='list ttu b white f4 cf', children=[
                html.Li(className='fl pl3', children=[
                    html.A(className='white link underline-hover',
                           href='http://www.threesixtygiving.org/contact/',
                           children='Contact'),
                ]),
                html.Li(className='fl pl3', children=[
                    html.A(className='white link underline-hover',
                           href='http://www.threesixtygiving.org/support/',
                           children='Support'),
                ]),
                html.Li(className='fl pl3', children=[
                    html.A(className='white link underline-hover',
                           href='http://www.threesixtygiving.org/news-2/',
                           children='News'),
                ]),
                html.Li(className='fl pl3', children=[
                    html.A(className='white link underline-hover',
                           href='http://www.threesixtygiving.org/support/standard/',
                           children='360Giving Standard'),
                ]),
            ]),
            html.P(className='white f4 tr mt3', children=[
                html.A(className='white link underline-hover b br b--white pr3 mr3',
                       href='tel:+442037525775',
                       children='020 3752 5775'),
                html.A(className='white link underline-hover',
                       href='mailto:info@threesixtygiving.org',
                       children='info@threesixtygiving.org'),
            ])
        ]),
    ]),
    html.Footer(className='pa3 bg-threesixty-grey cf bt b--threesixty-dark-green', children=[
        html.Div(className='cf', children=[
            html.P(className='white fl ma0', children=[
                '360Giving is a company limited by guarantee ',
                html.A(className='white link underline pointer',
                       href='https://beta.companieshouse.gov.uk/company/09668396',
                       children='09668396'),
                ' and a registered charity ',
                html.A(className='white link underline pointer',
                       href='http://beta.charitycommission.gov.uk/charity-details/?regid=1164883&subid=0',
                       children='1164883'),
            ]),
            html.A(className='white ostrich ttu fr f4 link',
                href='https://us10.campaign-archive.com/home/?u=216b8b926250184f90c7198e8&id=91870dde44',
                children='Sign up to our newsletter'),
        ]),
        html.Nav(className='', children=[
            html.Ul(className='list threesixty-mid-grey cf mt3 pl0', children=[
                html.Li(className='fl pr2 mr2 br b--threesixty-mid-grey', children=[
                    html.A(className='threesixty-mid-grey link underline-hover',
                           href='http://www.threesixtygiving.org/privacy/',
                           children='Privacy notice'),
                ]),
                html.Li(className='fl pr2 mr2 br b--threesixty-mid-grey', children=[
                    html.A(className='threesixty-mid-grey link underline-hover',
                           href='http://www.threesixtygiving.org/terms-conditions/',
                           children='Terms & Conditions'),
                ]),
                html.Li(className='fl pr2 mr2 br b--threesixty-mid-grey', children=[
                    html.A(className='threesixty-mid-grey link underline-hover',
                           href='http://www.threesixtygiving.org/cookie-policy/',
                           children='Cookie Policy'),
                ]),
                html.Li(className='fl pr2 mr2 br b--threesixty-mid-grey', children=[
                    html.A(className='threesixty-mid-grey link underline-hover',
                           href='http://www.threesixtygiving.org/take-down-policy/',
                           children='Take Down Policy'),
                ]),
                html.Li(className='fl pr2 mr2 br b--threesixty-mid-grey', children=[
                    html.A(className='threesixty-mid-grey link underline-hover',
                           href='https://creativecommons.org/licenses/by/4.0/',
                           children='License'),
                ]),
                html.Li(className='fl pr2 mr2 br b--threesixty-mid-grey', children=[
                    'Built by ',
                    html.A(className='threesixty-mid-grey link underline',
                           href='https://drkane.co.uk/',
                           children='David Kane'),
                    ' using ',
                    html.A(className='threesixty-mid-grey link underline',
                           href='https://dash.plot.ly/',
                           children='Dash by Plotly'),
                ]),
                html.Li(className='fl', children=[
                    html.A(className='threesixty-mid-grey link underline-hover',
                           href='https://github.com/ThreeSixtyGiving/explorer',
                           children='Github'),
                ]),
            ])
        ]),
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
