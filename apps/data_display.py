import json
import logging

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table_experiments as dt

from app import app
from load_data import get_filtered_df, get_from_cache, get_cache
from charts import *

DEFAULT_FILTERS = {
    "award_dates": {
        "min": 2015,
        "max": 2018
    },
    "grant_programmes": [
        {"label": "All grants", "value": "__all"}
    ],
    "funders": [
        {"label": "Funder", "value": "__all"}
    ]
}


layout = html.Div(id="dashboard-container", className='', children=[
    html.Div(className="", children=[

        html.Div(className="fl w-100 w-25-l pa2-l", children=[
            message_box(title="Filter data", contents=[
                html.Div(className="cf", children=[
                    html.Form(id="dashboard-filter", className='', children=[
                        html.Div(id='df-change-funder-wrapper', className='', children=[
                            html.Label(children='Funder'),
                            html.Div(className='cf mv3', children=[
                                dcc.Dropdown(
                                    id='df-change-funder',
                                    options=DEFAULT_FILTERS["funders"],
                                    multi=True,
                                    value=[DEFAULT_FILTERS["funders"][0]["value"]]
                                ),
                            ])
                        ]),

                        html.Div(id='df-change-grant-programme-wrapper', className='field', children=[
                            html.Label(children='Grant programme'),
                            html.Div(className='cf mv3', children=[
                                dcc.Dropdown(
                                    id='df-change-grant-programme',
                                    options=DEFAULT_FILTERS["grant_programmes"],
                                    multi=True,
                                    value=[DEFAULT_FILTERS["grant_programmes"][0]["value"]]
                                ),
                            ]),
                        ]),

                        html.Div(id='df-change-year-wrapper', className='field', children=[
                            html.Label(children='Data years'),
                            html.Div(className='cf ph3 mv3', children=[
                                dcc.RangeSlider(
                                    id='df-change-year',
                                    min=DEFAULT_FILTERS["award_dates"]["min"],
                                    max=DEFAULT_FILTERS["award_dates"]["max"],
                                    step=1,
                                    value=[DEFAULT_FILTERS["award_dates"]["min"],DEFAULT_FILTERS["award_dates"]["max"]],
                                    marks={"2015": "2015", "2018": "2018"}
                                ),
                            ])
                        ]),
                    ]),
                ]),
                html.Div(className="cf mt4", children=[
                    html.Div(dcc.Link(href='/', children='Select new data')),
                ]),
                html.Div(html.Pre(id='award-dates', children=json.dumps(DEFAULT_FILTERS, indent=4)), style={"display": "none"}),
            ])
        ]),

        html.Div(className="fl w-100 w-75-l pa2-l", children=[
            html.Div(id="dashboard-output", children=[], className='ui grid'),
        ]),
    ])
])


@app.callback(Output('dashboard-output', 'children'),
              [Input('df-change-grant-programme', 'value'),
               Input('df-change-funder', 'value'),
               Input('df-change-year', 'value'),
               Input('output-data-id', 'children')])
def dashboard_output(grant_programme, funder, year, fileid):
    df = get_filtered_df(fileid, grant_programme=grant_programme, funder=funder, year=year)
    logging.debug("dashboard_output", fileid, df is None)
    if df is None:
        return []

    outputs = []
    

    outputs.append(
        html.H2(className='normal', children=get_funder_output(df, grant_programme), id="funder-name")
    )
    outputs.append(get_statistics(df))

    charts = []

    charts.append(amount_awarded_chart(df))
    if "Grant Programme:Title" in df.columns:
        charts.append(grant_programme_chart(df))
    charts.append(awards_over_time_chart(df))
    charts.append(organisation_type_chart(df))
    charts.append(region_and_country_chart(df))
    charts.append(location_map(df))
    charts.append(organisation_age_chart(df))
    charts.append(organisation_income_chart(df))

    outputs.extend(charts)

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
    print("award_Dates_change", fileid)
    df = get_from_cache(fileid)
    logging.debug("award_dates_change", fileid, df is None)
    if df is None:
        return json.dumps(DEFAULT_FILTERS)
    return json.dumps({
        "award_dates": {
            "min": int(df["Award Date"].dt.year.min()),
            "max": int(df["Award Date"].dt.year.max()),
        },
        "grant_programmes": [
            {
                'label': '{} ({})'.format(i[0], i[1]), 
                'value': i[0]
            } for i in df["Grant Programme:Title"].value_counts().iteritems()
         ],
        "funders": [
            {
                'label': '{} ({})'.format(i[0], i[1]), 
                'value': i[0]
            } for i in df["Funding Org:Name"].value_counts().iteritems()
         ]
    }, indent=4)


@app.callback(Output('df-change-funder', 'options'),
              [Input('award-dates', 'children')])
def funder_dropdown(value):
    logging.debug("funder_dropdown", value)
    value = json.loads(value) if value else DEFAULT_FILTERS
    return value["funders"]


@app.callback(Output('df-change-funder-wrapper', 'style'),
              [Input('award-dates', 'children')],
              [State('df-change-funder-wrapper', 'style')])
def funder_dropdown_hide(value, existing_style):
    existing_style = {} if existing_style is None else existing_style
    value = json.loads(value) if value else DEFAULT_FILTERS
    if len(value["funders"])>1:
        if "display" in existing_style:
            del existing_style["display"]
    else:
        existing_style["display"] = 'none'
    return existing_style



@app.callback(Output('df-change-grant-programme', 'options'),
              [Input('award-dates', 'children')])
def grant_programme_dropdown(value):
    logging.debug("grant_programme_dropdown", value)
    value = json.loads(value) if value else DEFAULT_FILTERS
    return value["grant_programmes"]


@app.callback(Output('df-change-grant-programme-wrapper', 'style'),
              [Input('award-dates', 'children')],
              [State('df-change-grant-programme-wrapper', 'style')])
def grant_programme_dropdown_hide(value, existing_style):
    existing_style = {} if existing_style is None else existing_style
    value = json.loads(value) if value else DEFAULT_FILTERS
    if len(value["grant_programmes"])>1:
        if "display" in existing_style:
            del existing_style["display"]
    else:
        existing_style["display"] = 'none'
    return existing_style
    

@app.callback(Output('df-change-year', 'min'),
              [Input('award-dates', 'children')])
def year_select_min(value):
    logging.debug("year_select_min", value)
    value = json.loads(value) if value else DEFAULT_FILTERS
    return value["award_dates"]["min"]
    

@app.callback(Output('df-change-year', 'max'),
              [Input('award-dates', 'children')])
def year_select_max(value):
    logging.debug("year_select_max", value)
    value = json.loads(value) if value else DEFAULT_FILTERS
    return value["award_dates"]["max"]
    

@app.callback(Output('df-change-year', 'marks'),
              [Input('award-dates', 'children')])
def year_select_marks(value):
    logging.debug("year_select_marks", value)
    value = json.loads(value) if value else DEFAULT_FILTERS
    step = 3 if (value["award_dates"]["max"] - value["award_dates"]["min"]) > 6 else 1
    min_max = range(value["award_dates"]["min"], value["award_dates"]["max"] + 1, step)
    return {str(i): str(i) for i in min_max}
    

@app.callback(Output('df-change-year', 'value'),
              [Input('award-dates', 'children')])
def year_select_value(value):
    logging.debug("year_select_value", value)
    value = json.loads(value) if value else DEFAULT_FILTERS
    return [value["award_dates"]["min"], value["award_dates"]["max"]]
    


@app.callback(Output('df-change-year-wrapper', 'style'),
              [Input('award-dates', 'children')],
              [State('df-change-year-wrapper', 'style')])
def year_hide(value, existing_style):
    existing_style = {} if existing_style is None else existing_style
    value = json.loads(value) if value else DEFAULT_FILTERS
    if value["award_dates"]["min"] != value["award_dates"]["max"]:
        if "display" in existing_style:
            del existing_style["display"]
    else:
        existing_style["display"] = 'none'
    return existing_style
