import os

import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly.graph_objs as go
import inflect
import humanize
import babel.numbers


DEFAULT_TABLE_FIELDS = ["Title", "Description", "Amount Awarded", 
                        "Award Date", "Recipient Org:Name", 
                        "Grant Programme:Title"]
THREESIXTY_COLOURS = ['#9c2061', '#f48320', '#cddc2b', '#53aadd']

MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN")
MAPBOX_STYLE = os.environ.get("MAPBOX_STYLE", 'mapbox://styles/davidkane/cjmtr1n101qlz2ruqszjcmhls')

def chart_title(title, subtitle=None, description=None):
    return html.Figcaption(className='', children=[
        html.H3(className='f4 mv0', children=title),
        (html.P(className='f5 gray mv0', children=subtitle) if subtitle else None),
        (dcc.Markdown(className='', children=description) if description else None),
    ])

def chart_wrapper(chart, title, subtitle=None, description=None):
    return html.Figure(className='ph0 mh0', children=[
        chart_title(title, subtitle, description),
        chart
    ])

def message_box(title, contents, error=False):
    border = 'b--red' if error else 'b--black'
    background = 'bg-red' if error else 'bg-black'
    if isinstance(contents, str):
        contents_div = dcc.Markdown(
            className='f6 f5-ns lh-copy mv0', children=contents)
    else:
        contents_div = html.P(
            className='f6 f5-ns lh-copy mv0', children=contents),

    return html.Div(className='center hidden ba mb4 {}'.format(border), children=[
        html.H1(className='f4 white mv0 pv2 ph3 {}'.format(background),
                children=title),
        html.Div(className='pa3', children=contents_div),
    ])

def get_bar_data(values, name="Grants", chart_type='bar', colour=0):
    titles = [i[0] for i in values.iteritems()]
    titles = [" - ".join(get_unique_list(i)) if isinstance(i, (list, tuple)) else i for i in titles]
    bar_data = {
        'x': titles, 
        'y': [i[1] for i in values.iteritems()], 
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

def get_unique_list(l):
    # from https://stackoverflow.com/a/37163210/715621
    used = set()
    return [x.strip() for x in l if x.strip() not in used and (used.add(x.strip()) or True)]

def grant_programme_chart(df):

    if "Grant Programmes:Title" not in df.columns or len(df["Grant Programmes:Title"].unique()) <= 1:
        return

    return chart_wrapper(
        dcc.Graph(
            id="grant_programme_chart",
            figure={
                'data': [get_bar_data(df["Grant Programme:Title"].value_counts())],
                'layout': {
                    'yaxis': {
                        'automargin': True,
                    },
                    'xaxis': {
                        'automargin': True,
                    },
                }
            }
        ),
        'Grant programmes', 
        '(number of grants)'
    )


def amount_awarded_chart(df):
    return chart_wrapper(
        dcc.Graph(
            id="amount_awarded_chart",
            figure={
                'data': [get_bar_data(df["Amount Awarded:Bands"].value_counts().sort_index())],
                'layout': {
                    'font': {
                        'family': '"Source Sans Pro",sans-serif;'
                    },
                    'yaxis': {
                        'automargin': True,
                    },
                    'xaxis': {
                        'automargin': True,
                    },
                }
            }
        ),
        'Amount awarded',
        '(number of grants)',
    )

def awards_over_time_chart(df):

    data = [dict(
        x = df['Award Date'],
        autobinx = False,
        autobiny = True,
        marker = dict(color = THREESIXTY_COLOURS[1]),
        name = 'date',
        type = 'histogram',
        xbins = dict(
            start='{}-01-01'.format(df['Award Date'].dt.year.min()),
            end='{}-12-31'.format(df['Award Date'].dt.year.max()),
            size = 'M1',
        )
    )]

    updatemenus = [dict(
        x = 0.1,
        y = 1.15,
        xref = 'paper',
        yref = 'paper',
        yanchor = 'top',
        active = 0,
        showactive = True,
        buttons = [
        dict(
            args = ['xbins.size', 'M1'],
            label = 'by month',
            method = 'restyle',
        ), dict(
            args = ['xbins.size', 'M3'],
            label = 'by quarter',
            method = 'restyle',
        ), dict(
            args = ['xbins.size', 'M12'],
            label = 'by year',
            method = 'restyle',
        )]
    )]

    return chart_wrapper(
        dcc.Graph(
            id="awards_over_time_chart",
            figure={
                'data': data,
                'layout': {
                    'yaxis': {'automargin': True},
                    'xaxis': {'automargin': True},
                    'updatemenus': updatemenus
                }
            } 
        ),
        'Award Date',
        '(number of grants)'
    )


def region_and_country_chart(df):
    values = df.fillna({"__geo_ctry": "Unknown", "__geo_rgn": "Unknown"}).groupby(["__geo_ctry", "__geo_rgn"]).agg({
        "Amount Awarded": "sum",
        "Title": "size"
    })
    return chart_wrapper(
        dcc.Graph(
            id="region_and_country_chart",
            figure={
                'data': [get_bar_data(values["Title"], chart_type='column', colour=2)],
                'layout': {
                    'yaxis': {
                        'automargin': True,
                    },
                    'xaxis': {
                        'automargin': True,
                    },
                }
            } 
        ),
        'Region and Country',
        '(number of grants)',
        description='''Based on the registered address of a charity or company
(or a postcode if included with the grant data). Only available for registered
charities or companies, or those grants which contain a postcode.'''
    )

def organisation_type_chart(df):
    values = df["__org_org_type"].fillna("Unknown").value_counts().sort_index()
    return chart_wrapper(
        dcc.Graph(
            id="organisation_type_chart",
            figure={
                "data": [go.Pie(
                    labels=[i[0] for i in values.iteritems()],
                    values=[i[1] for i in values.iteritems()],
                    hole=0.4,
                    marker={
                        'colors': THREESIXTY_COLOURS
                    },
                    insidetextfont={
                        'color': 'white'
                    }
                    )],
                'layout': {
                    'yaxis': {
                        'automargin': True,
                    },
                    'xaxis': {
                        'automargin': True,
                    },
                }
            }
        ),
        'Recipient type',
        '(proportion of grants)'
    )


def organisation_income_chart(df):
    if df["__org_latest_income_bands"].count() == 0:
        return message_box(
            'Could not show organisation income chart',
            '''This chart can\'t be shown as there are no recipients in the data with 
income data. If your data contains grants to charities, you can add charity
numbers to your data to show a chart of their latest income.
            ''',
            error=True
        )
    return chart_wrapper(
        dcc.Graph(
            id="organisation_income_chart",
            figure={
                'data': [get_bar_data(df["__org_latest_income_bands"].value_counts().sort_index(), colour=3)],
                'layout': {
                    'yaxis': {
                        'automargin': True,
                    },
                    'xaxis': {
                        'automargin': True,
                    },
                }
            } 
        ),
        'Latest income of charity recipients',
        '(number of grants)',
    )

def organisation_age_chart(df):
    if df["__org_age_bands"].count()==0:
        return message_box(
            'Could not show organisation age chart',
            '''This chart can\'t be shown as there are no recipients in the data with 
organisation age data. Add company or charity numbers to your data to show a chart of
the age of organisations.
            ''',
            error=True
        )
    return chart_wrapper(
        dcc.Graph(
            id="organisation_age_chart",
            figure={
                'data': [get_bar_data(df["__org_age_bands"].value_counts().sort_index())],
                'layout': {
                    'yaxis': {
                        'automargin': True,
                    },
                    'xaxis': {
                        'automargin': True,
                    },
                }
            }
        ),
        'Age of recipients',
        '(number of grants)',
        description='Based only on recipients with charity or company numbers.'
    )


def location_map(df):

    if not MAPBOX_ACCESS_TOKEN:
        return

    popup_col = 'Recipient Org:Name'
    if popup_col not in df.columns and 'Recipient Org:Identifier' in df.columns:
        popup_col = 'Recipient Org:Identifier'

    try:
        geo = df[["__geo_lat", "__geo_long", popup_col]].dropna().drop_duplicates()
    except KeyError as e:
        return message_box(
            'Location map',
            [
                '''An error occured when attempting to show the map. Error: ''',
                html.Pre(str(e))
            ],
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
            text=geo[popup_col].values,
        )
    ]

    layout = go.Layout(
        autosize=True,
        height=800,
        hovermode='closest',
        mapbox=dict(
            accesstoken=MAPBOX_ACCESS_TOKEN,
            bearing=0,
            center=dict(
                lat=54.093409,
                lon=-2.89479
            ),
            pitch=0,
            zoom=5,
            style=MAPBOX_STYLE
        ),
    )

    return chart_wrapper(
        dcc.Graph(id='grant_location_chart', figure={"data": data, "layout": layout}),
        'Location of grant recipients',
        description='''Based on the registered address of a charity or company
(or a postcode if included with the grant data). Only available for registered
charities or companies, or those grants which contain a postcode.'''
    )

def dataframe_datatable(df, max_length=50, fields=DEFAULT_TABLE_FIELDS):
    rows = df.sample(max_length) if len(df)>max_length else df
    return dt.DataTable(
        rows=rows.reset_index()[fields].to_dict('records'), 
        id="df-datatable",
        editable=False,
        row_selectable=False
    )

def get_statistics(df):
    amount_awarded = df.groupby("Currency").sum()["Amount Awarded"]
    amount_awarded = [format_currency(amount, currency) for currency, amount in amount_awarded.items()]

    return html.Div(
        className='flex statistics',
        children=[
            html.Div(className='pa5 tc white bg-red', children=[
                html.Div(className='b f2', children="{:,.0f}".format(len(df))),
                html.Div(className='', children=pluralize("grant", len(df)))
            ]),
            html.Div(className='pa5 tc white bg-red', children=[
                html.Div(className='b f2', children="{:,.0f}".format(df["Recipient Org:Identifier"].unique().size)),
                html.Div(className='', children=pluralize("recipient", df["Recipient Org:Identifier"].unique().size))
            ])
        ] + [
            html.Div(className='pa5 tc white bg-red', children=[
                html.Div(className='b f2', children=i[0]),
                html.Div(className='', children=i[1])
            ]) for i in amount_awarded
        ]
    )

def format_currency(amount, currency='GBP', humanize_=True, int_format="{:,.0f}"):
    if humanize_:
        amount_str = humanize.intword(amount).split(" ")
        if len(amount_str) == 2:
            return (
                babel.numbers.format_currency(float(amount_str[0]), currency, format="¤#,##0.0", currency_digits=False), 
                amount_str[1]
            )

    return (
        babel.numbers.format_currency(amount, currency, format="¤#,##0", currency_digits=False), 
        ""
    )


def get_funder_output(df, grant_programme=[]):
    
    funders = list_to_string(df["Funding Org:Name"].unique().tolist())
    
    years = {
        "max": df["Award Date"].dt.year.max(),
        "min": df["Award Date"].dt.year.min(),
    }
    if years["max"] == years["min"]:
        years = " in {}".format(years["max"])
    else:
        years = " between {} and {}".format(years["min"], years["max"])

    return_str = [
        html.Span("{} made by ".format(pluralize("Grant", len(df)))),
        html.Strong(funders, className='pa1 white bg-threesixty-two'),
        html.Span(" {}".format(years)),
    ]

    # if grant_programme and '__all' not in grant_programme:
    #     return [
    #         return_str,
    #         html.Div(children="({})".format(list_to_string(grant_programme)))
    #     ]

    return return_str

    

def list_to_string(l, oxford_comma='auto', separator=", "):
    if len(l)==1:
        return l[0]
    # if oxford_comma == "auto" then if any items contain "and" it is set to true
    if oxford_comma=="auto":
        if len([x for x in l if " and " in x]):
            oxford_comma=True
        else:
            oxford_comma=False
    return "{}{} and {}".format(
        ", ".join(l[0:-1]),
        ", " if oxford_comma else "",
        l[-1]
    )

def pluralize(string, count):
    p = inflect.engine()
    return p.plural(string, count)
