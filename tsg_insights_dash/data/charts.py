import os
import copy

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd

from tsg_insights.data.utils import list_to_string, pluralize, get_unique_list, format_currency
from .results import CHARTS

DEFAULT_TABLE_FIELDS = ["Title", "Description", "Amount Awarded", 
                        "Award Date", "Recipient Org:0:Name", 
                        "Grant Programme:0:Title"]
THREESIXTY_COLOURS = ['#9c2061', '#f48320', '#cddc2b', '#53aadd']
DEFAULT_LAYOUT = {
    'font': {
        'family': 'neusa-next-std-compact, "Source Sans Pro", sans-serif;',
        'size': 18
    },
    'yaxis': {
        'automargin': True,
        'visible': False,
        'showgrid': False,
        'showline': False,
        'linewidth': 0,
        'tickfont': {
            'size': 20
        },
    },
    'xaxis': {
        'automargin': True,
        'showgrid': False,
        'showline': False,
        'linewidth': 0,
        'tickfont': {
            'size': 20
        },
    },
    'margin': go.layout.Margin(
        l=40,
        r=24,
        b=40,
        t=24,
        pad=4
    ),
}

def chart_title(title, subtitle=None, description=None):
    return html.Figcaption(className='', children=[
        html.H2(className='results-page__body__section-title', children=title),
        (html.P(className='', children=subtitle) if subtitle else None),
        (dcc.Markdown(className='', children=description) if description else None),
    ])

def chart_wrapper(chart, title, subtitle=None, description=None):
    return html.Figure(className='', children=[
        chart_title(title, subtitle, description),
        chart
    ])

def message_box(title, contents, error=False):
    if isinstance(contents, str):
        contents_div = dcc.Markdown(
            className='', children=contents)
    else:
        contents_div = html.P(
            className='', children=contents),

    return html.Div(className='', children=[
        html.H2(className='results-page__body__section-title',
                children=title),
        html.Div(className='', children=contents_div),
    ])

def get_bar_data(values, name="Grants", chart_type='bar', colour=0):
    titles = [i[0] for i in values.iteritems()]
    titles = [" - ".join(get_unique_list(i)) if isinstance(i, (list, tuple)) else i for i in titles]
    bar_data = {
        'x': titles, 
        'y': [i[1] for i in values.iteritems()], 
        'text': [i[1] for i in values.iteritems()],
        'textposition': 'auto',
        'constraintext': 'inside',
        'textfont': {
            'size': 18,
            'family': 'neusa-next-std-compact, sans-serif;',
        },
        'type': chart_type, 
        'name': name,
        'marker': {
            'color': THREESIXTY_COLOURS[colour]
        },
        'fill': 'tozeroy',
    }
    if chart_type=='column':
        bar_data['type'] = 'bar'
        bar_data['orientation'] = 'h'
        x = bar_data['x']
        bar_data['x'] = bar_data['y']
        bar_data['y'] = x
    return bar_data

def funder_chart(df):

    data = CHARTS['funders']['get_results'](df)
    if len(data) <= 1:
        return

    return chart_wrapper(
        dcc.Graph(
            id="funding_org_chart",
            figure={
                'data': [get_bar_data(data)],
                'layout': DEFAULT_LAYOUT
            },
            config={
                'displayModeBar': False
            }
        ),
        'Funders', 
        '(number of grants)'
    )


def grant_programme_chart(df):

    if "Grant Programmes:Title" not in df.columns or len(df["Grant Programmes:Title"].unique()) <= 1:
        return

    data = CHARTS['grant_programmes']['get_results'](df)

    return chart_wrapper(
        dcc.Graph(
            id="grant_programme_chart",
            figure={
                'data': [get_bar_data(data)],
                'layout': DEFAULT_LAYOUT
            },
            config={
                'displayModeBar': False
            }
        ),
        'Grant programmes',
        '(number of grants)'
    )


def amount_awarded_chart(df):
    data = CHARTS['amount_awarded']['get_results'](df)
    return chart_wrapper(
        dcc.Graph(
            id="amount_awarded_chart",
            figure={
                'data': [get_bar_data(data)],
                'layout': DEFAULT_LAYOUT
            },
            config={
                'displayModeBar': False
            }
        ),
        'Amount awarded',
        '(number of grants)',
    )

def org_identifier_chart(df):
    data = CHARTS['identifier_scheme']['get_results'](df)
    return chart_wrapper(
        dcc.Graph(
            id="identifier_scheme_chart",
            figure={
                'data': [get_bar_data(data)],
                'layout': DEFAULT_LAYOUT
            },
            config={
                'displayModeBar': False
            }
        ),
        'Identifier scheme',
        '(number of grants)',
    )

def awards_over_time_chart(df):

    # check whether all grants were awarded in the same month
    if df["Award Date"].max().strftime("%Y-%m") == df["Award Date"].min().strftime("%Y-%m"):
        return message_box(
            'Award Date',
            'All grants were awarded in {}.'.format(df["Award Date"].min().strftime("%B %Y")),
            error=False
        )

    data = CHARTS['award_date']['get_results'](df)

    xbins_sizes = (
        ('M1', 'by month'),
        ('M3', 'by quarter'),
        ('M12', 'by year')
    )

    xbins_size = 'M1'
    if (data['max'] - data['min']) >= 5:
        xbins_size = 'M12'
    elif (data['max'] - data['min']) >= 1:
        xbins_size = 'M3'

    data = [dict(
        x = data['all'],
        autobinx = False,
        autobiny=True,
        marker = dict(color = THREESIXTY_COLOURS[1]),
        name = 'date',
        type = 'histogram',
        xbins = dict(
            start='{}-01-01'.format(data['min']),
            end='{}-12-31'.format(data['max']),
            size=xbins_size,
        )
    )]

    updatemenus = [dict(
        x = 0.1,
        y = 1.15,
        xref = 'paper',
        yref = 'paper',
        yanchor = 'top',
        active=[b[0] for b in xbins_sizes].index(xbins_size),
        showactive = True,
        buttons = [
            dict(
                args = ['xbins.size', b[0]],
                label = b[1],
                method = 'restyle',
            ) 
            for b in xbins_sizes
        ]
    )]

    layout = copy.deepcopy(DEFAULT_LAYOUT)
    layout['updatemenus'] = updatemenus
    layout['yaxis']['visible'] = True
    layout['yaxis']['showline'] = False

    return chart_wrapper(
        dcc.Graph(
            id="awards_over_time_chart",
            figure={
                'data': data,
                'layout': layout
            },
            config={
                'displayModeBar': False
            }
        ),
        'Award Date',
        '(number of grants)'
    )


def region_and_country_chart(df):
    data = CHARTS['ctry_rgn']['get_results'](df)

    if not data or (df["__geo_ctry"].count() + df["__geo_rgn"].count()) == 0:
        return message_box(
            'Region and Country',
            '''This chart can\'t be shown as there are no recipients in the data with 
income data. If your data contains grants to charities, you can add charity
numbers to your data to show a chart of their latest income.
            ''',
            error=True
        )

    layout = copy.deepcopy(DEFAULT_LAYOUT)
    layout['yaxis']['visible'] = True
    layout['xaxis']['visible'] = False

    return chart_wrapper(
        dcc.Graph(
            id="region_and_country_chart",
            figure={
                'data': [get_bar_data(data["Grants"], chart_type='column', colour=2)],
                'layout': layout
            },
            config={
                'displayModeBar': False
            }
        ),
        'Region and Country',
        '(number of grants)',
        description='''Based on the registered address of a charity or company
(or a postcode if included with the grant data). Only available for registered
charities or companies, or those grants which contain a postcode.'''
    )


def organisation_type_chart(df):
    data = CHARTS['org_type']['get_results'](df)
    title = 'Recipient type'
    subtitle = '(number of grants)'
    description = '''Organisation type is only available for recipients with a valid
                           organisation identifier.'''

    if len(data) > 4:
        layout = copy.deepcopy(DEFAULT_LAYOUT)
        layout['yaxis']['visible'] = True
        layout['xaxis']['visible'] = False
        return chart_wrapper(
            dcc.Graph(
                id="organisation_type_chart",
                figure={
                    'data': [get_bar_data(data.sort_values(), chart_type='column')],
                    'layout': layout
                },
                config={
                    'displayModeBar': False
                }
            ),
            title, subtitle, description=description
        )


    return chart_wrapper(
        dcc.Graph(
            id="organisation_type_chart",
            figure={
                "data": [go.Pie(
                    labels=[i[0] for i in data.iteritems()],
                    values=[i[1] for i in data.iteritems()],
                    hole=0.4,
                    marker={
                        'colors': THREESIXTY_COLOURS
                    },
                    insidetextfont={
                        'color': 'white'
                    }
                    )],
                'layout': DEFAULT_LAYOUT
            },
            config={
                'displayModeBar': False
            }
        ),
        title, subtitle, description=description
    )


def organisation_income_chart(df):
    if "__org_latest_income_bands" not in df.columns or df["__org_latest_income_bands"].count() == 0:
        return message_box(
            'Latest income of charity recipients',
            '''This chart can\'t be shown as there are no recipients in the data with 
organisation income data. Add company or charity numbers to your data to show a chart of
the income of organisations.
            ''',
            error=True
        )

    data = CHARTS['org_income']['get_results'](df)
    return chart_wrapper(
        dcc.Graph(
            id="organisation_income_chart",
            figure={
                'data': [get_bar_data(data, colour=3)],
                'layout': DEFAULT_LAYOUT
            },
            config={
                'displayModeBar': False
            }
        ),
        'Latest income of charity recipients',
        '(number of grants)',
    )

def organisation_age_chart(df):
    if "__org_age_bands" not in df.columns or df["__org_age_bands"].count()==0:
        return message_box(
            'Age of recipient organisations',
            '''This chart can\'t be shown as there are no recipients in the data with 
organisation age data. Add company or charity numbers to your data to show a chart of
the age of organisations.
            ''',
            error=True
        )

    data = CHARTS['org_age']['get_results'](df)
    return chart_wrapper(
        dcc.Graph(
            id="organisation_age_chart",
            figure={
                'data': [get_bar_data(data)],
                'layout': DEFAULT_LAYOUT
            },
            config={
                'displayModeBar': False
            }
        ),
        'Age of recipient organisations',
        '(number of grants)',
        description='Organisation age uses the registration date of that organisation. Based only on recipients with charity or company numbers.'
    )

def imd_chart(df):
    # @TODO: expand to include non-English IMD too
    data = CHARTS['org_age']['get_results'](df)
    if not data:
        return message_box(
            'Index of multiple deprivation',
            '''We can't show this chart as we couldn't find any details of the index of multiple deprivation 
            ranking for postcodes in your data. At the moment we can only use data for England.
            ''',
            error=True
        )

    layout = copy.deepcopy(DEFAULT_LAYOUT)
    layout['xaxis']['type'] = 'category'
    
    return chart_wrapper(
        dcc.Graph(
            id="imd_chart",
            figure={
                'data': [get_bar_data(data)],
                'layout': layout
            },
            config={
                'displayModeBar': False
            }
        ),
        'Index of multiple deprivation',
        '(number of grants)',
            description='''Shows the number of grants made in each decile of deprivation in England, 
            from 1 (most deprived) to 10 (most deprived). Based on the postcode included with the grant
            or on an organisation's registered postcode, so may not reflect where grant activity took place.'''
    )

def location_map(df, mapbox_access_token=None, mapbox_style=None):

    if not mapbox_access_token:
        return

    if "__geo_lat" not in df.columns or "__geo_long" not in df.columns:
        return

    popup_col = 'Recipient Org:0:Name'
    if popup_col not in df.columns and 'Recipient Org:0:Identifier' in df.columns:
        popup_col = 'Recipient Org:0:Identifier'

    try:
        geo = df[["__geo_lat", "__geo_long", popup_col]].dropna()
        grant_count = len(geo)
        geo = geo.groupby(["__geo_lat", "__geo_long", popup_col]).size().rename("grants").reset_index()
    except KeyError as e:
        return message_box(
            'Location of grant recipients',
            [
                '''An error occured when attempting to show the map. Error: ''',
                html.Pre(str(e))
            ],
            error=True
        )

    if len(geo) == 0:
        return message_box(
            'Location of grant recipients',
            '''Map cannot be shown. No location data is available.''',
            error=True
        )
        
    data = [
        go.Scattermapbox(
            lat=geo["__geo_lat"].values,
            lon=geo["__geo_long"].values,
            mode='markers',
            marker=dict(
                size=9,
                color=THREESIXTY_COLOURS[0]
            ),
            text=geo.apply(
                lambda row: "{} ({} grants)".format(row[popup_col], row['grants']) if row["grants"] > 1 else row[popup_col],
                axis=1
            ).values,
        )
    ]

    layout = go.Layout(
        autosize=True,
        height=800,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=54.093409,
                lon=-2.89479
            ),
            pitch=0,
            zoom=5,
            style=mapbox_style
        ),
        margin=go.layout.Margin(
            l=0,
            r=0,
            b=0,
            t=0,
            pad=0
        ),
    )

    return chart_wrapper(
        dcc.Graph(
            id='grant_location_chart',
            figure={"data": data, "layout": layout},
            config={
                'displayModeBar': False
            }
        ),
        'Location of grant recipients',
        description='''Showing the location of **{:,.0f}** grants out of {:,.0f}
        
Based on the registered address of a charity or company
(or a postcode if included with the grant data). Only available for UK registered
charities or companies, or those grants which contain a postcode.'''.format(
            grant_count, len(df)
)
    )

def get_statistics(df):
    amount_awarded = df.groupby("Currency").sum()["Amount Awarded"]
    amount_awarded = [format_currency(amount, currency) for currency, amount in amount_awarded.items()]

    return html.Div(
        className='results-page__body__content__spheres',
        children=[
            html.Div(
                className='results-page__body__content__sphere',
                style={'backgroundColor': '#9c1f61'},
                children=[
                    html.P(className='', children="{:,.0f}".format(len(df))),
                    html.H4(className='', children=pluralize("grant", len(df)))
                ]
            ),
            html.Div(
                className='results-page__body__content__sphere',
                style={'backgroundColor': '#f4831f'},
                children=[
                    html.P(className='', children="{:,.0f}".format(df["Recipient Org:0:Identifier"].unique().size)),
                    html.H4(className='', children=pluralize("recipient", df["Recipient Org:0:Identifier"].unique().size))
                ]
            ),
        ] + [
            html.Div(
                className='results-page__body__content__sphere',
                style={'backgroundColor': '#50aae4'},
                children=[
                    html.P(className='', children=i[0]),
                    html.H4(className='', children=i[1])
                ]
            ) for i in amount_awarded
        ]
    )

def get_funder_output(df, grant_programme=[]):
    
    funder_class = ''
    funder_names = sorted(df["Funding Org:0:Name"].unique().tolist())
    subtitle = []
    if len(funder_names)>5:
        funders = html.Span("{:,.0f} funders".format(len(funder_names)), className=funder_class)
        subtitle = [html.Div(className='mt2 gray f4',
                             children=list_to_string(funder_names))]
    else:
        funders = list_to_string(
            [html.Span(f, className=funder_class)
             for f in funder_names],
            as_list=True
        )
    
    years = {
        "max": df["Award Date"].dt.year.max(),
        "min": df["Award Date"].dt.year.min(),
    }
    if years["max"] == years["min"]:
        years = [
            " in ",
            html.Span(
                className='results-page__body__content__date',
                children=str(years["max"])
            ),
        ]
    else:
        years = [
            " between ",
            html.Span(
                className='results-page__body__content__date',
                children=" {} and {}".format(years["min"], years["max"])
            ),
        ]

    # if grant_programme and '__all' not in grant_programme:
    #     return [
    #         return_str,
    #         html.Div(children="({})".format(list_to_string(grant_programme)))
    #     ]

    return_str = [
        html.H5(
            className='results-page__body__content__grants-made-by',
            children="{} made by ".format(pluralize("Grant", len(df)))
        ),
        html.H1(
            className='results-page__body__content__header',
            children=[html.Span(
                className='results-page__body__content__title',
                style={'opacity': '1'},
                children=funders
            )] + years
        ),
    ]

    # @todo: STYLING FOR subbtitle listing funders
    # return return_str + subtitle
    return return_str
