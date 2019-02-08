import logging
import re

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table_experiments as dt

from app import app
from load_data import get_filtered_df, get_from_cache, get_cache
from charts import *
from filters import FILTERS
from tsg_insights_components import InsightChecklist, InsightDropdown, InsightFoldable

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
        return InsightChecklist(
            id=filter_id,
            ulClassName="results-page__menu__checkbox",
            style={"maxHeight": "217px"},
            options=filter_def["defaults"],
            value=[filter_def["defaults"][0]["value"]]
        )

    if filter_def.get("type") == 'dropdown':
        return InsightDropdown(
            id=filter_id,
            options=filter_def["defaults"],
            multi=False,
            value=[filter_def["defaults"][0]["value"]],
            className="results-page__menu__select-list__wrapper",
            selectClassName="results-page__menu__select-list",
        )


layout = html.Div(id="dashboard-container", className='results-page', children=[
    html.Div(className='results-page__header', children=[
        html.Div(className='wrapper', children=[
            "360Giving ",
            html.Span(style={"color": "#9c1f61"}, children="Insights"),
            html.Span(style={"color": "rgba(11, 40, 51, 0.3)"}, children="Beta"),
        ]),
    ]),
    html.Div(className='results-page__app', children=[
        html.Aside(className='results-page__menu', children=[
            dcc.Link(
                className='results-page__menu__back',
                href='/',
                children=[
                    html.I(className='material-icons', children='arrow_back'),
                    " Select another dataset",
                ]
            ),
            html.H3(className='results-page__menu__section-title', children='Filters'),
            html.Form(id='filters-form', children=[
                # @TODO: turn these into new filters
                html.Div(className="cf", children=[
                    html.Form(id="dashboard-filter", className='', children=[
                        InsightFoldable(
                            id='df-change-{}-wrapper'.format(filter_id),
                            className='results-page__menu__subsection',
                            titleClassName='results-page__menu__subsection-title js-foldable js-foldable-more',
                            titleUnfoldedClassName='js-foldable-less',
                            title=filter_def.get('label', filter_id),
                            valueClassName='results-page__menu__subsection-value',
                            valueStyle={'maxHeight': '16px'},
                            value="",
                            children=[
                                filter_html('df-change-{}'.format(filter_id), filter_def),
                            ]
                        ) for filter_id, filter_def in FILTERS.items()
                    ]),
                ]),
                dcc.Store(id='award-dates', data={f: FILTERS[f]["defaults"] for f in FILTERS}),
            ]),
        ]),

        html.Div(className="results-page__body", children=[
            html.Section(className='results-page__body__content',
                         id="dashboard-output")
        ]),
    ]),
])


@app.callback(Output('dashboard-output', 'children'),
              [Input('output-data-id', 'data')] + [
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
    

    outputs.extend(get_funder_output(df, filter_args.get("grant_programmes")))
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

    outputs.extend(charts)

    # outputs.append(html.Div(className='flex flex-wrap', children=charts))

    return outputs

@app.callback(Output('award-dates', 'data'),
              [Input('output-data-id', 'data')])
def award_dates_change(fileid):
    df = get_from_cache(fileid)
    logging.debug("award_dates_change", fileid, df is None)
    if df is None:
        return {f: FILTERS[f]["defaults"] for f in FILTERS}

    return {f: FILTERS[f]["get_values"](df) for f in FILTERS}

# ================
# Functions that return a function to be used in callbacks
# ================


def dropdown_filter(filter_id, filter_def):
    def dropdown_filter_func(value):
        logging.debug("dropdown", filter_id, filter_def, value)
        value = value if value else {filter_id: filter_def["defaults"]}
        return value[filter_id]
    return dropdown_filter_func


def filter_dropdown_hide(filter_id, filter_def):
    def filter_dropdown_hide_func(value, existing_style):
        existing_style = {} if existing_style is None else existing_style
        value = value if value else {filter_id: filter_def["defaults"]}
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
        value = value if value else {filter_id: filter_def["defaults"]}
        return value[filter_id]["min"]
    return slider_select_min_func
        
def slider_select_max(filter_id, filter_def):
    def slider_select_max_func(value):
        logging.debug("year_select_max", value)
        value = value if value else {filter_id: filter_def["defaults"]}
        return value[filter_id]["max"]
    return slider_select_max_func

def slider_select_marks(filter_id, filter_def):
    def slider_select_marks_func(value):
        logging.debug("year_select_marks", value)
        value = value if value else {filter_id: filter_def["defaults"]}
        step = 3 if (value[filter_id]["max"] - value[filter_id]["min"]) > 6 else 1
        min_max = range(value[filter_id]["min"], value[filter_id]["max"] + 1, step)
        return {str(i): str(i) for i in min_max}
    return slider_select_marks_func
        
def slider_select_value(filter_id, filter_def):
    def slider_select_value_func(value):
        logging.debug("year_select_value", value)
        value = value if value else {filter_id: filter_def["defaults"]}
        return [value[filter_id]["min"], value[filter_id]["max"]]
    return slider_select_value_func

def slider_hide(filter_id, filter_def):
    def slider_hide_func(value, existing_style):
        existing_style = {} if existing_style is None else existing_style
        value = value if value else {filter_id: filter_def["defaults"]}
        if value[filter_id]["min"] != value[filter_id]["max"]:
            if "display" in existing_style:
                del existing_style["display"]
        else:
            existing_style["display"] = 'none'
        return existing_style
    return slider_hide_func

def set_dropdown_value(filter_id, filter_def):
    def set_dropdown_value_fund(value, options):
        if filter_def.get("type")=="rangeslider":
            if value[0] == value[1]:
                return str(value[0])
            else:
                return "{} to {}".format(value[0], value[1])

        value_labels = [re.sub(r' \([0-9,]+\)$', "", o['label'])
                        for o in options if o['value'] in value]
        if len(value_labels) == 0:
            return filter_def.get("defaults", [{}])[0].get("label")
        elif len(value_labels) == 1:
            return value_labels[0]
        elif len(value_labels) <= 3:
            return ", ".join(value_labels)
        return "Multiple options selected"
    return set_dropdown_value_fund

# Add callbacks for all the filters
for filter_id, filter_def in FILTERS.items():

    # callback to update the text showing filtered options next to the filter
    app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'value'),
                    [Input('df-change-{}'.format(filter_id), 'value')],
                    [State('df-change-{}'.format(filter_id), 'options')])(
        set_dropdown_value(filter_id, filter_def)
    )

    if filter_def.get("type") in ['dropdown', 'multidropdown']:

        # callback adding the filter itself
        app.callback(
            Output('df-change-{}'.format(filter_id), 'options'),
            [Input('award-dates', 'data')])(
                dropdown_filter(filter_id, filter_def)
            )

        # callback which hides the filter if there's only 1 or 0 options available
        app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'style'),
                    [Input('award-dates', 'data')],
            [State('df-change-{}-wrapper'.format(filter_id), 'style')])(
                filter_dropdown_hide(filter_id, filter_def)
            )

    elif filter_def.get("type") in ['rangeslider']:

        # callback setting the minimum value of a slider
        app.callback(Output('df-change-{}'.format(filter_id), 'min'),
                    [Input('award-dates', 'data')])(
                        slider_select_min(filter_id, filter_def)
                    )
            
        # callback setting the maximum value of a slider
        app.callback(Output('df-change-{}'.format(filter_id), 'max'),
                    [Input('award-dates', 'data')])(
                        slider_select_max(filter_id, filter_def)
                    )
            
        # callback setting the marks shown on a slider
        app.callback(Output('df-change-{}'.format(filter_id), 'marks'),
                    [Input('award-dates', 'data')])(
                        slider_select_marks(filter_id, filter_def)
                    )

        # callback for setting the initial value of a slider
        app.callback(Output('df-change-{}'.format(filter_id), 'value'),
                    [Input('award-dates', 'data')])(
                        slider_select_value(filter_id, filter_def)
                    )

        # callback which hides the filter if there's only 1 or 0 options available
        app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'style'),
                    [Input('award-dates', 'data')],
                    [State('df-change-{}-wrapper'.format(filter_id), 'style')])(
                        slider_hide(filter_id, filter_def)
                    )
