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
        # <div class="js-foldable-target js-foldable-target-3 js-foldable-foldTarget" style="text-align: right; max-height: 33px;">
        #   <fieldset style="display:inline-block;">
        #     <ul class="results-page__menu__range-select js-range-select-dateAwarded">
        #         <li>
        #           <input id="dateAwarded-1" type="checkbox" name="dateAwarded" value="2014" checked="" class="show-label">
        #           <label for="dateAwarded-1">
        #             2014
        #           </label>
        #         </li>
        #     </ul>
        #   </fieldset>
        # </div>
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
        # <fieldset class="js-foldable-target js-foldable-target-1 js-foldable-foldTarget" style="max-height: 217px;">
        #   <ul class="results-page__menu__checkbox">
        #       <li>
        #         <input id="regionAndCountry-england-east" type="checkbox" name="regionAndCountry" value="england-east">
        #         <label for="regionAndCountry-england-east">
        #           England - East of England (3)
        #         </label>
        #       </li>
        #   </ul>
        # </fieldset>
        return dcc.Dropdown(
            id=filter_id,
            options=filter_def["defaults"],
            multi=True,
            value=[filter_def["defaults"][0]["value"]]
        )

    if filter_def.get("type") == 'dropdown':
        # <div class="results-page__menu__select-list__wrapper js-foldable-target js-foldable-target-2 js-foldable-foldTarget" style="max-height: 31px;">
        #   <select id="funders" name="funders" class="results-page__menu__select-list">          
        #       <option value="arcadia">Arcadia</option>
        #   </select>
        # </div>
        return dcc.Dropdown(
            id=filter_id,
            options=filter_def["defaults"],
            multi=False,
            value=[filter_def["defaults"][0]["value"]]
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
                        html.Div(
                            id='df-change-{}-wrapper'.format(filter_id),
                            className='results-page__menu__subsection',
                            children=[
                                html.H4(
                                    className='results-page__menu__subsection-title js-foldable js-foldable-aim-1 js-foldable-more',
                                    children=filter_def.get('label', filter_id),
                                ),
                                html.H5(
                                    className='results-page__menu__subsection-value js-foldable-target js-folgable-opposite-target js-foldable-target-1',
                                    style={'maxHeight': '16px'},
                                    id='df-change-{}-results'.format(filter_id),
                                    children="",
                                ),
                                filter_html('df-change-{}'.format(filter_id), filter_def),
                            ])
                         for filter_id, filter_def in FILTERS.items()
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
    charts.append(imd_chart(df))
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

for filter_id, filter_def in FILTERS.items():

    if filter_def.get("type") in ['dropdown', 'multidropdown']:
        app.callback(
            Output('df-change-{}'.format(filter_id), 'options'),
            [Input('award-dates', 'data')])(
                dropdown_filter(filter_id, filter_def)
            )

        app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'style'),
                    [Input('award-dates', 'data')],
            [State('df-change-{}-wrapper'.format(filter_id), 'style')])(
                filter_dropdown_hide(filter_id, filter_def)
            )

    elif filter_def.get("type") in ['rangeslider']:
        app.callback(Output('df-change-{}'.format(filter_id), 'min'),
                    [Input('award-dates', 'data')])(
                        slider_select_min(filter_id, filter_def)
                    )
            
        app.callback(Output('df-change-{}'.format(filter_id), 'max'),
                    [Input('award-dates', 'data')])(
                        slider_select_max(filter_id, filter_def)
                    )
            
        app.callback(Output('df-change-{}'.format(filter_id), 'marks'),
                    [Input('award-dates', 'data')])(
                        slider_select_marks(filter_id, filter_def)
                    )
            
        app.callback(Output('df-change-{}'.format(filter_id), 'value'),
                    [Input('award-dates', 'data')])(
                        slider_select_value(filter_id, filter_def)
                    )
            
        app.callback(Output('df-change-{}-wrapper'.format(filter_id), 'style'),
                    [Input('award-dates', 'data')],
                    [State('df-change-{}-wrapper'.format(filter_id), 'style')])(
                        slider_hide(filter_id, filter_def)
                    )
