import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State

from app import app

from tsg_insights_dash import data_display
from tsg_insights.data.cache import get_cache

import requests_cache

requests_cache.install_cache(backend='redis', connection=get_cache())

app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', className='cf', children=data_display.layout),
    dcc.Store(id='output-data-id'),
])

@app.callback(Output('output-data-id', 'data'),
              [Input('url', 'pathname')])
def update_file_id(pathname):
    if pathname and pathname.startswith("/file/"):
        fileid = pathname.replace("/file/", "")
        return fileid

server = app.server

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    app.run_server(debug=True)
