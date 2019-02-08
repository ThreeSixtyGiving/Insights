import os
import copy

import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly.graph_objs as go
import inflect
import humanize
import babel.numbers
import pandas as pd


DEFAULT_TABLE_FIELDS = ["Title", "Description", "Amount Awarded", 
                        "Award Date", "Recipient Org:Name", 
                        "Grant Programme:Title"]
THREESIXTY_COLOURS = ['#9c2061', '#f48320', '#cddc2b', '#53aadd']

MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN")
MAPBOX_STYLE = os.environ.get("MAPBOX_STYLE", 'mapbox://styles/davidkane/cjmtr1n101qlz2ruqszjcmhls')
DEFAULT_LAYOUT = {
    'font': {
        'family': '"Source Sans Pro",sans-serif;'
    },
    'titlefont': {
        'family': '"Source Sans Pro",sans-serif;'
    },
    'yaxis': {
        'automargin': True,
    },
    'xaxis': {
        'automargin': True,
    },
    'margin': go.layout.Margin(
        l=40,
        r=0,
        b=40,
        t=0,
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
    border = 'b--red' if error else 'b--black'
    background = 'bg-red' if error else 'bg-black'
    if isinstance(contents, str):
        contents_div = dcc.Markdown(
            className='f6 f5-ns lh-copy mv0', children=contents)
    else:
        contents_div = html.P(
            className='f6 f5-ns lh-copy mv0', children=contents),

    return html.Div(className='center hidden ba mb4 {}'.format(border), children=[
        html.H1(className='f4 white mv0 pv2 ph3 ostrich {}'.format(background),
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

def funder_chart(df):

    funders = df["Funding Org:Name"].value_counts()
    if len(funders) <= 1:
        return

    return chart_wrapper(
        dcc.Graph(
            id="funding_org_chart",
            figure={
                'data': [get_bar_data(funders)],
                'layout': DEFAULT_LAYOUT
            }
        ),
        'Funders', 
        '(number of grants)'
    )


def grant_programme_chart(df):

    if "Grant Programmes:Title" not in df.columns or len(df["Grant Programmes:Title"].unique()) <= 1:
        return

    return chart_wrapper(
        dcc.Graph(
            id="grant_programme_chart",
            figure={
                'data': [get_bar_data(df["Grant Programme:Title"].value_counts())],
                'layout': DEFAULT_LAYOUT
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
                'layout': DEFAULT_LAYOUT
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

    layout = {
        'updatemenus': updatemenus
    }
    for i in DEFAULT_LAYOUT:
        layout[i] = DEFAULT_LAYOUT[i]

    return chart_wrapper(
        dcc.Graph(
            id="awards_over_time_chart",
            figure={
                'data': data,
                'layout': layout
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
                'layout': DEFAULT_LAYOUT
            } 
        ),
        'Region and Country',
        '(number of grants)',
        description='''Based on the registered address of a charity or company
(or a postcode if included with the grant data). Only available for registered
charities or companies, or those grants which contain a postcode.'''
    )

def organisation_type_chart(df):
    values = df["__org_org_type"].fillna("No organisation identifier").value_counts().sort_index()
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
                'layout': DEFAULT_LAYOUT
            }
        ),
        'Recipient type',
        '(proportion of grants)',
        description='''Organisation type is only available for recipients with a valid
organisation identifier.'''
    )


def organisation_income_chart(df):
    if df["__org_latest_income_bands"].count() == 0:
        return message_box(
            'Latest income of charity recipients',
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
                'layout': DEFAULT_LAYOUT
            } 
        ),
        'Latest income of charity recipients',
        '(number of grants)',
    )

def organisation_age_chart(df):
    if df["__org_age_bands"].count()==0:
        return message_box(
            'Age of recipient organisations',
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
                'layout': DEFAULT_LAYOUT
            }
        ),
        'Age of recipient organisations',
        '(number of grants)',
        description='Organisation age uses the registration date of that organisation. Based only on recipients with charity or company numbers.'
    )

def imd_chart(df):
    # @TODO: expand to include non-English IMD too
    df.to_pickle("test_imd.pkl")
    imd = df.loc[df['__geo_ctry']=='England', '__geo_imd']
    if imd.count()==0:
        return message_box(
            'Index of multiple deprivation',
            '''We can't show this chart as we couldn't find any details of the index of multiple deprivation 
            ranking for postcodes in your data. At the moment we can only use data for England.
            ''',
            error=True
        )
    
    # maximum rank of LSOAs by IMD
    # from: https://www.arcgis.com/sharing/rest/content/items/0a404beab6f544be8fb72d0c2b12d62b/data
    # NSPL user guid
    # 1 = most deprived, this number = most deprived
    imd_total_eng = 32844
    imd_total_scot = 6976
    imd_total_wal = 1909
    imd_total_ni = 890

    # work out the IMD decile
    imd = ((imd / imd_total_eng) * 10).apply(pd.np.ceil).value_counts().sort_index().reindex(
        pd.np.arange(1, 11)
    ).fillna(0)

    imd.index = pd.Series([
        '1: most deprived', '2', '3', '4', '5', '6', '7', '8', '9', '10: least deprived'
    ])

    layout = copy.deepcopy(DEFAULT_LAYOUT)
    layout['xaxis']['type'] = 'category'
    
    return chart_wrapper(
        dcc.Graph(
            id="imd_chart",
            figure={
                'data': [get_bar_data(imd)],
                'layout': layout
            }
        ),
        'Index of multiple deprivation',
        '(number of grants)',
        description='''Shows the number of grants made in each decile of deprivation in England, 
        from 1 (most deprived) to 10 (most deprived). Based on the postcode included with the grant
        or on an organisation's registered postcode, so may not reflect where grant activity took place.'''
    )

def location_map(df):

    if not MAPBOX_ACCESS_TOKEN:
        return

    popup_col = 'Recipient Org:Name'
    if popup_col not in df.columns and 'Recipient Org:Identifier' in df.columns:
        popup_col = 'Recipient Org:Identifier'

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
        margin=go.layout.Margin(
            l=0,
            r=0,
            b=0,
            t=0,
            pad=0
        ),
    )

    return chart_wrapper(
        dcc.Graph(id='grant_location_chart', figure={"data": data, "layout": layout}),
        'Location of grant recipients',
        description='''Showing the location of **{:,.0f}** grants out of {:,.0f}
        
Based on the registered address of a charity or company
(or a postcode if included with the grant data). Only available for registered
charities or companies, or those grants which contain a postcode.'''.format(
            grant_count, len(df)
)
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
                    html.P(className='', children="{:,.0f}".format(df["Recipient Org:Identifier"].unique().size)),
                    html.H4(className='', children=pluralize("recipient", df["Recipient Org:Identifier"].unique().size))
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

def format_currency(amount, currency='GBP', humanize_=True, int_format="{:,.0f}", abbreviate=False):
    abbreviations = {
        'million': 'M',
        'billion': 'bn'
    }

    if humanize_:
        amount_str = humanize.intword(amount).split(" ")
        if len(amount_str) == 2:
            return (
                babel.numbers.format_currency(
                    float(amount_str[0]),
                    currency,
                    format="¤#,##0.0",
                    currency_digits=False,
                    locale='en_UK'
                ), 
                abbreviations.get(
                    amount_str[1], amount_str[1]) if abbreviate else amount_str[1]
            )

    return (
        babel.numbers.format_currency(
            amount,
            currency,
            format="¤#,##0",
            currency_digits=False,
            locale='en_UK'
        ),
        ""
    )


def get_funder_output(df, grant_programme=[]):
    
    funder_class = ''
    funder_names = sorted(df["Funding Org:Name"].unique().tolist())
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

    

def list_to_string(l, oxford_comma='auto', separator=", ", as_list=False):
    if len(l)==1:
        return l[0]
    # if oxford_comma == "auto" then if any items contain "and" it is set to true
    if oxford_comma=="auto":
        if len([x for x in l if " and " in x]):
            oxford_comma=True
        else:
            oxford_comma=False

    if as_list:
        return_list = [l[0]]
        for i in l[1:-1]:
            return_list.append(i)
            return_list.append(separator)
        if oxford_comma:
            return_list.append(separator)
        return_list.append(" and ")
        return_list.append(l[-1])
        return return_list

    return "{}{} and {}".format(
        separator.join(l[0:-1]),
        separator if oxford_comma else "",
        l[-1]
    )

def pluralize(string, count):
    p = inflect.engine()
    return p.plural(string, count)
