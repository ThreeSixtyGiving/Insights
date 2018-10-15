import json
import logging

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table_experiments as dt

from app import app
from load_data import get_filtered_df, get_from_cache, get_cache
from charts import *
from filters import FILTERS

def filter_html(filter_id, filter_def):
    if filter_def.get("type") == 'rangeslider':
        min_ = filter_def["defaults"].get("min", 0)
        max_ = filter_def["defaults"].get("max", 100)
        step_ = filter_def["defaults"].get("step", 1)
        return dcc.RangeSlider(
            id=filter_id,
            min=min_,
            max=max_,
            step=step_,
            value=[min_,max_],
            marks={str(min_): str(min_), str(max_): str(max_)}
        )

    if filter_def.get("type") == 'multidropdown':
        return dcc.Dropdown(
            id=filter_id,
            options=filter_def["defaults"],
            multi=True,
            value=[filter_def["defaults"][0]["value"]]
        )

    if filter_def.get("type") == 'dropdown':
        return dcc.Dropdown(
            id=filter_id,
            options=filter_def["defaults"],
            multi=False,
            value=[filter_def["defaults"][0]["value"]]
        )


layout = html.Div(id="dashboard-container", className='', children=[
    html.Div(className="fl w-100 w-25-l pa2-l", children=[
        message_box(title="Filter data", contents=[
            html.Div(className="cf", children=[
                html.Form(id="dashboard-filter", className='', children=[
                    html.Div(id='df-change-{}-wrapper'.format(filter_id), className='', children=[
                        html.Label(children=filter_def.get('label', filter_id)),
                        html.Div(className='cf mv3', children=[
                            filter_html('df-change-{}'.format(filter_id), filter_def)
                        ])
                    ]) for filter_id, filter_def in FILTERS.items()
                ]),
            ]),
            html.Div(className="cf mt4", children=[
                html.Div(dcc.Link(href='/', children='Select new data')),
            ]),
            html.Div(
                html.Pre(
                    id='award-dates', 
                    children=json.dumps({f: FILTERS[f]["defaults"] for f in FILTERS}, indent=4)
                ), 
                style={"display": "none"}
            ),
        ])
    ]),

    html.Div(className="fl w-100 w-75-l pa2-l", children=[
        html.Article(id="dashboard-output", children=[], className=''),
    ]),
])


@app.callback(Output('dashboard-output', 'children'),
              [Input('output-data-id', 'children')] + [
                  Input('df-change-{}'.format(f), 'value')
                  for f in FILTERS
              ])
def dashboard_output(fileid, *args):
    filter_args = dict(zip(FILTERS.keys(), args))
    df = get_filtered_df(fileid, **filter_args)
    logging.debug("dashboard_output", fileid, df is None)
    if df is None:
        return []

    if len(df) == 0:
        return html.Div('No grants meet criteria')

    outputs = []
    

    outputs.append(
        html.H2(className='f2 mt0 mb4 lh-copy ostrich',
                children=get_funder_output(df, filter_args.get("grant_programmes")), id="funder-name")
    )
    outputs.append(get_statistics(df))

    charts = []

    charts.append(funder_chart(df))
    charts.append(amount_awarded_chart(df))
    charts.append(grant_programme_chart(df))
    charts.append(awards_over_time_chart(df))
    charts.append(organisation_type_chart(df))
    charts.append(region_and_country_chart(df))
    charts.append(location_map(df))
    charts.append(organisation_age_chart(df))
    charts.append(organisation_income_chart(df))

    outputs.append(html.Div(className='flex flex-wrap', children=charts))

    # row = []
    # for i in charts:
    #     outputs.
    #     # if len(row)==2:
    #     #     outputs.append(html.Div(className='row', children=row))
    #     #     row = []
    #     row.append(html.Div(className='sixteen wide column', children=i))
    # if row:
    #     outputs.append(html.Div(className='row', children=row))

        
    # outputs.append(
    #     html.Div(className='row', children=[
    #         html.Div(className='column', children=[dataframe_datatable(df)])
    #     ])
    # )

    return outputs

@app.callback(Output('award-dates', 'children'),
              [Input('output-data-id', 'children')])
def award_dates_change(fileid):
    df = get_from_cache(fileid)
    logging.debug("award_dates_change", fileid, df is None)
    if df is None:
        return json.dumps({f: FILTERS[f]["defaults"] for f in FILTERS})

    return json.dumps({f: FILTERS[f]["get_values"](df) for f in FILTERS}, indent=4)

# ================
# Functions that return a function to be used in callbacks
# ================


def dropdown_filter(filter_id, filter_def):
    def dropdown_filter_func(value):
        logging.debug("dropdown", filter_id, filter_def, value)
        value = json.loads(value) if value else {filter_id: filter_def["defaults"]}
        return value[filter_id]
    return dropdown_filter_func


def filter_dropdown_hide(filter_id, filter_def):
    def filter_dropdown_hide_func(value, existing_style):
        existing_style = {} if existing_style is None else existing_style
        value = json.loads(value) if value else {filter_id: filter_def["defaults"]}
        if len(value[filter_id])>1:
            if "display" in existing_style:
                del existing_style["display"]
        else:
            existing_style["display"] = 'none'
        return existing_style
    return filter_dropdown_hide_func
    
def slider_select_min(filter_id, filter_def):
    def slider_select_min_func(value):
        logging.debug("year_select_min", value)
        value = json.loads(value) if value else {filter_id: filter_def["defaults"]}
        return value[filter_id]["min"]
    return slider_select_min_func
        
def slider_select_max(filter_id, filter_def):
    def slider_select_max_func(value):
        logging.debug("year_select_max", value)
        value = json.loads(value) if value else {filter_id: filter_def["defaults"]}
        return value[filter_id]["max"]
    return slider_select_max_func

def slider_select_marks(filter_id, filter_def):
    def slider_select_marks_func(value):
        logging.debug("year_select_marks", value)
        value = json.loads(value) if value else {filter_id: filter_def["defaults"]}
        step = 3 if (value[filter_id]["max"] - value[filter_id]["min"]) > 6 else 1
        min_max = range(value[filter_id]["min"], value[filter_id]["max"] + 1, step)
        return {str(i): str(i) for i in min_max}
    return slider_select_marks_func
        
def slider_select_value(filter_id, filter_def):
    def slider_select_value_func(value):
        logging.debug("year_select_value", value)
        value = json.loads(value) if value else {filter_id: filter_def["defaults"]}
        return [value[filter_id]["min"], value[filter_id]["max"]]
    return slider_select_value_func

def slider_hide(filter_id, filter_def):
    def slider_hide_func(value, existing_style):
        existing_style = {} if existing_style is None else existing_style
        value = json.loads(value) if value else {filter_id: filter_def["defaults"]}
        if value[filter_id]["min"] != value[filter_id]["max"]:
            if "display" in existing_style:
                del existing_style["display"]
        else:
            existing_style["display"] = 'none'
        return existing_style
    return slider_hide_func

for filter_id, filter_def in FILTERS.items():

    if filter_def.get("type") in ['dropdown', 'multidropdown']:
        app.callback(
            Output('df-change-{}'.format(filter_id), 'options'),
            [Input('award-dates', 'children')])(
                dropdown_filter(filter_id, filter_def)
            )

        app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'style'),
                    [Input('award-dates', 'children')],
            [State('df-change-{}-wrapper'.format(filter_id), 'style')])(
                filter_dropdown_hide(filter_id, filter_def)
            )

    elif filter_def.get("type") in ['rangeslider']:
        app.callback(Output('df-change-{}'.format(filter_id), 'min'),
                    [Input('award-dates', 'children')])(
                        slider_select_min(filter_id, filter_def)
                    )
            
        app.callback(Output('df-change-{}'.format(filter_id), 'max'),
                    [Input('award-dates', 'children')])(
                        slider_select_max(filter_id, filter_def)
                    )
            
        app.callback(Output('df-change-{}'.format(filter_id), 'marks'),
                    [Input('award-dates', 'children')])(
                        slider_select_marks(filter_id, filter_def)
                    )
            
        app.callback(Output('df-change-{}'.format(filter_id), 'value'),
                    [Input('award-dates', 'children')])(
                        slider_select_value(filter_id, filter_def)
                    )
            
        app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'style'),
                    [Input('award-dates', 'children')],
                    [State('df-change-{}-wrapper'.format(filter_id), 'style')])(
                        slider_hide(filter_id, filter_def)
                    )
