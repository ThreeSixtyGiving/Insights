import logging
import re
import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML as InnerHTML
from flask import url_for, render_template

from app import app
from tsg_insights.data.cache import get_from_cache, get_cache, get_metadata_from_cache
from .data.charts import *
from .data.filters import FILTERS, get_filtered_df
from tsg_insights_components import InsightChecklist, InsightDropdown, InsightFoldable

def footer(server):
    with server.app_context():
        return InnerHTML(render_template('footer.html.j2', footer_class="light"))

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
            html.A(
                href='/',
                children=[
                    "360Giving ",
                    html.Span(style={"color": "#9c1f61"}, children="Insights"),
                    html.Span(style={"color": "rgba(11, 40, 51, 0.3)"}, children="Beta"),
                ]
            )
        ]),
    ]),
    html.Div(className='results-page__app', children=[
        html.Aside(className='results-page__menu', children=[
            html.A(
                className='results-page__menu__back',
                href='/?file-selection-modal',
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
                            container=dict(
                                className='results-page__menu__subsection',
                            ),
                            title=dict(
                                value=filter_def.get('label', filter_id),
                                className='results-page__menu__subsection-title js-foldable js-foldable-more',
                                unfoldedClassName='js-foldable-less',
                            ),
                            value=dict(
                                value="",
                                className='results-page__menu__subsection-value js-foldable-target',
                                foldedClassName='js-foldable-foldTarget',
                                style={'maxHeight': '16px'},
                            ),
                            child=dict(
                                className='js-foldable-target',
                                foldedClassName='js-foldable-foldTarget',
                            ),
                            children=[
                                filter_html('df-change-{}'.format(filter_id), filter_def),
                            ]
                        ) for filter_id, filter_def in FILTERS.items()
                    ] + [
                        html.Div(className="results-page__menu__subsection", children=[
                            html.A(id='df-reset-filters', href='#',
                                   className='results-page__menu__reset', children='Reset all filters')
                        ]),
                        html.Div(className="results-page__menu__subsection", children=[
                            html.P(className='results-page__menu__feedback', children=[
                                'Tell us what you think',
                                html.Br(),
                                html.A(href='mailto:labs@threesixtygiving.org',
                                       children='labs@threesixtygiving.org'),
                            ]),
                        ])
                    ]),
                ]),
                dcc.Store(id='award-dates', data={f: FILTERS[f]["defaults"] for f in FILTERS}),
            ]),
        ]),

        html.Div(className="results-page__body", children=[
            html.Section(className='results-page__body__content',
                         id="dashboard-output"),
            html.Section(
                className='results-page__body__whats-next',
                id="whats-next",
                children=[]
            ),
            footer(app.server),
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

    metadata = get_metadata_from_cache(fileid)

    if df is None:
        return [
            html.H1(
                html.Span("Dataset not found",
                          className="results-page__body__content__date"),
                    className="results-page__body__content__header"),
            html.P(([
                html.A("Try to fetch this file", href="/?fetch={}".format(fileid)),
                " or "
            ] if fileid else []) + [
                html.A("Go to homepage",
                       href="/"),
            ], className="results-page__body__section-description"),
        ]

    if len(df) == 0:
        return html.Div('No grants meet criteria')

    outputs = []
    
    outputs.extend(get_funder_output(df, filter_args.get("grant_programmes")))
    outputs.append(get_statistics(df))
    outputs.extend(get_file_output(metadata))

    charts = []
    
    charts.append(funder_chart(df))
    charts.append(amount_awarded_chart(df))
    charts.append(grant_programme_chart(df))
    charts.append(awards_over_time_chart(df))
    charts.append(organisation_type_chart(df))
    # charts.append(org_identifier_chart(df))
    charts.append(region_and_country_chart(df))
    charts.append(location_map(
        df,
        app.server.config.get("MAPBOX_ACCESS_TOKEN"),
        app.server.config.get("MAPBOX_STYLE")
    ))
    charts.append(organisation_age_chart(df))
    charts.append(organisation_income_chart(df))
    # charts.append(imd_chart(df))

    outputs.extend(charts)

    return outputs

@app.callback(Output('file-download-csv', 'href'),
              [Input('output-data-id', 'data')])
def file_download_csv_href(fileid):
    return url_for('data.download_file', fileid=fileid, format='csv')

@app.callback(Output('file-download-excel', 'href'),
              [Input('output-data-id', 'data')])
def file_download_excel_href(fileid):
    return url_for('data.download_file', fileid=fileid, format='xlsx')


@app.callback(Output('whats-next', 'children'),
              [Input('output-data-id', 'data')])
def what_next_missing_fields(fileid):
    df = get_filtered_df(fileid)

    if df is None:
        return []

    missing = []
    if (df["__geo_ctry"].count() + df["__geo_rgn"].count()) == 0:
        missing.append(["postcodes or other geo data",
                        "https://postcodes.findthatcharity.uk/"])

    org_type = CHARTS['org_type']['get_results'](df)
    if "Identifier not recognised" in org_type.index and len(org_type.index)==1:
        missing.append(["external organisation identifiers, like charity numbers",
                        'http://standard.threesixtygiving.org/en/latest/identifiers/#id2'])


    if not missing:
        missing = [
            html.P([
                html.Strong('1. Make the most of your data'),
                html.Br(),
                '''Grants data is at its most powerful when you can link it to other datasets.
                   By including postcodes and organisation identifiers we've been able to
                   map and link this data to other datasets.''',
            ]),
        ]
    else:
        missing = [
            html.P([
                html.Strong('1. Make the most of your data'),
                html.Br(),
                '''Grants data is at its most powerful when you can link it to other datasets.
                    There were some pieces missing from the data you selected which meant we couldn't
                    make the most of it. For linkable data, we suggest adding, wherever possible:''',
                ]),
            html.Ul([
                html.Li([
                    html.A(m[0], href=m[1])
                ]) for m in missing
            ]),
            html.P([
                html.A(
                    '''360Giving can help you add these fields to your data.''',
                    href="https://www.threesixtygiving.org/support/"
                ),
            ]),
        ]

    print(missing)

    return [
        html.H3(className="results-page__body__whats-next__title",
                children='What next?'),
        html.Div(missing),
        html.P([
            html.Strong(
                '2. Try other services and get inspiration'),
            html.Br(),
            '''There are lots of other services you can use to explore and visualise this kind of data. Here are some of our favourites:''',
        ]),
        html.Ul([
            html.Li(
                [html.A('Flourish', href='https://flourish.studio/')]),
            html.Li(
                [html.A('Databasic', href='https://databasic.io/')]),
            html.Li([html.A('Carto', href='https://carto.com/')]),
            html.Li(
                [html.A('360Giving Visualisation challenge', href='https://challenge.threesixtygiving.org/')]),
        ]),
        html.P([
            html.Strong('3. Do your own analysis'),
            html.Br(),
            '''You can also download the data generated by 360Insights to analyse yourself, for example in Excel
                            or another software. The download includes all the additional information we've added to the data,
                            like charity data or geo data from the postcodes.''',
        ]),
        html.Ul([
            html.Li(html.A(href='#', target="_blank",
                        children='CSV Download', id='file-download-csv')),
            html.Li(html.A(href='#', target="_blank",
                        children='Excel Download', id='file-download-excel')),
        ]),
        html.P([
            '''Fields added by this tool start with "Insights:"''',
        ]),
        html.P([
            html.Strong('4. Give us feedback!'),
            html.Br(),
            '''If you liked this tool, found a bug or want to add features to it, send us an
                            email to ''',
            html.A('labs@threesixtygiving.org',
                href='mailto:labs@threesixtygiving.org'),
        ]),
    ]

@app.callback(Output('award-dates', 'data'),
              [Input('output-data-id', 'data')])
def award_dates_change(fileid):
    df = get_from_cache(fileid)
    logging.debug("award_dates_change", fileid, df is None)
    if df is None:
        return {f: FILTERS[f]["defaults"] for f in FILTERS}

    try:
        return {f: FILTERS[f]["get_values"](df) for f in FILTERS}
    except Exception as e:
        return {f: FILTERS[f]["defaults"] for f in FILTERS}

# ================
# Functions that return a function to be used in callbacks
# ================


def dropdown_filter(filter_id, filter_def):
    def dropdown_filter_func(value):
        logging.debug("dropdown", filter_id, filter_def, value)
        value = value if value else {filter_id: filter_def["defaults"]}
        return value[filter_id]
    return dropdown_filter_func

def dropdown_filter_value(filter_id, filter_def):
    def dropdown_filter_set_default_value(value, n_clicks, existing_value):
        logging.debug("dropdown", n_clicks)
        if n_clicks:
            return ['__all']
        return existing_value
    return dropdown_filter_set_default_value

def filter_dropdown_hide(filter_id, filter_def):
    def filter_dropdown_hide_func(value, container):
        if 'style' not in container:
            container['style'] = {}
        value = value if value else {filter_id: filter_def["defaults"]}
        if len(value[filter_id])>1:
            if "display" in container['style']:
                del container['style']["display"]
        else:
            container['style']["display"] = 'none'
        return container
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
    def slider_select_value_func(value, n_clicks, existing_value):
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
    def set_dropdown_value_fund(value, options, existingvaluedef):
        if filter_def.get("type")=="rangeslider":
            if value[0] == value[1]:
                existingvaluedef['value'] = str(value[0])
            else:
                existingvaluedef['value'] = "{} to {}".format(
                    value[0], value[1])
            return existingvaluedef

        value_labels = [re.sub(r' \([0-9,]+\)$', "", o['label'])
                        for o in options if o['value'] in value]
        if len(value_labels) == 0:
            existingvaluedef['value'] = filter_def.get("defaults", [{}])[
                0].get("label")
        elif len(value_labels) == 1:
            existingvaluedef['value'] = value_labels[0]
        elif len(value_labels) <= 3:
            existingvaluedef['value'] = ", ".join(value_labels)
        else:
            existingvaluedef['value'] = "Multiple options selected"
        return existingvaluedef
    return set_dropdown_value_fund

# Add callbacks for all the filters
for filter_id, filter_def in FILTERS.items():

    # callback to update the text showing filtered options next to the filter
    app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'value'),
                    [Input('df-change-{}'.format(filter_id), 'value')],
                    [State('df-change-{}'.format(filter_id), 'options'),
                     State('df-change-{}-wrapper'.format(filter_id), 'value')])(
        set_dropdown_value(filter_id, filter_def)
    )

    if filter_def.get("type") in ['dropdown', 'multidropdown']:

        # callback adding the filter itself
        app.callback(
            Output('df-change-{}'.format(filter_id), 'options'),
            [Input('award-dates', 'data')])(
                dropdown_filter(filter_id, filter_def)
            )

        # callback setting the default value of the filter (nothing selected)
        app.callback(
            Output('df-change-{}'.format(filter_id), 'value'),
            [Input('award-dates', 'data'),
             Input('df-reset-filters', 'n_clicks')],
            [State('df-change-{}'.format(filter_id), 'value')])(
                dropdown_filter_value(filter_id, filter_def)
            )

        # callback which hides the filter if there's only 1 or 0 options available
        app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'container'),
                    [Input('award-dates', 'data')],
                     [State('df-change-{}-wrapper'.format(filter_id), 'container')])(
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
                     [Input('award-dates', 'data'),
                      Input('df-reset-filters', 'n_clicks')],
                     [State('df-change-{}'.format(filter_id), 'value')])(
                        slider_select_value(filter_id, filter_def)
                    )

        # callback which hides the filter if there's only 1 or 0 options available
        app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'style'),
                    [Input('award-dates', 'data')],
                    [State('df-change-{}-wrapper'.format(filter_id), 'style')])(
                        slider_hide(filter_id, filter_def)
                    )
