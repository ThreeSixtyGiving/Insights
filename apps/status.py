import hashlib
import os
import json
import io
import datetime
import dateutil.parser

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_resumable_upload

import pandas as pd
import babel.numbers
import humanize

from app import app
from load_data import get_registry_by_publisher, get_registry
from charts import pluralize, format_currency

FILE_TYPES = {
    "xlsx": ("Excel", "Microsoft Excel"),
    "xls": ("Excel", "Microsoft Excel (pre 2007)"),
    "csv": ("CSV", "Comma Separated Values"),
    "json": ("JSON", "JSON is a structured file format"),
}

layout = html.Div(id="status-container", className='', children=[
    html.Form(className='', children=[
        html.Div(className='ui input', children=[
            dcc.Input(id='status-search', placeholder='Search', type='text')
        ]),
        dcc.Dropdown(id='status-licence', multi=True, options=[]),
        html.Div(className='field', children=[
            html.Label('Last updated'),
            dcc.Dropdown(id='status-last-modified', options=[
                {'label': 'All publishers', 'value': '__all'},
                {'label': 'In the last month', 'value': 'lastmonth'},
                {'label': 'In the last 6 months', 'value': '6month'},
                {'label': 'In the last year', 'value': '12month'},
            ]),
        ]),
    ]),
    html.Div(id='status-rows', children=[], className='ui very relaxed items'),
])

@app.callback(Output('status-licence', 'options'),
              [Input('status-container', 'children')])
def get_status_options(_):
    reg = get_registry()
    licenses = {}
    for r in reg:
        if r.get('license') and r.get('license') in licenses:
            continue
        licenses[r.get('license')] = r.get('license_name')
    return [{
        "label": v,
        "value": k
    } for k, v in licenses.items()]


@app.callback(Output('status-rows', 'children'),
              [Input('status-search', 'value'),
               Input('status-licence', 'value'),
               Input('status-last-modified', 'value')])
def update_status_container(search, licence, last_modified):
    print("update_status_container", search, licence, last_modified)
    reg = get_registry_by_publisher(filters={
        "search": search,
        "licence": licence,
        "last_modified": last_modified
    })
    rows = []
    for pub, pub_reg in reg.items():
        rows.append(
            html.Div(className='item', children=[
                html.Div(className='ui small image', children=[
                    html.Img(src=pub_reg[0].get("publisher", {}).get("logo")),
                ]),
                html.Div(className='content', children=[
                    html.A(className='header', 
                        href=pub_reg[0].get("publisher", {}).get("website"),
                        target='_blank', children=[
                        pub_reg[0].get("publisher", {}).get("name")
                    ]),
                    html.Div(className='meta', children=([
                        html.Span(className="", children=[
                            "{} {}".format(len(pub_reg), pluralize("file", len(pub_reg)))
                        ]),
                        html.Span('·'),
                    ] + get_publisher_stats(pub_reg, separator=html.Span('·')) if len(pub_reg)>1 else [])
                    ),
                    html.Div(className='description ui cards', children=[
                        file_row(v, len(pub_reg)) for v in pub_reg
                    ])
                ])
            ], style={"margin-bottom": "48px"})
        )
    return rows

def file_row(v, files=1):
    style = {"border-top": '0'} if files > 1 else {}

    validity = {
        'valid': {'class': '', 'icon': None, 'messages': {
            'positive': 'Valid data', 'negative': 'Data invalid'
        }, 'message': 'Validity unknown'},
        'downloads': {'class': '', 'icon': None, 'messages': {
            'positive': 'Download link working', 'negative': 'Download link broken'
        }, 'message': 'Download link not checked'},
        'acceptable_license': {'class': '', 'icon': None, 'messages': {
            'positive': 'Licensed for reuse', 'negative': 'Licence doesn\'t allow reuse'
        }, 'message': 'Unknown licence'},
    }
    for i in validity:
        if v.get('datagetter_metadata', {}).get(i)==True:
            validity[i]['class'] = 'positive'
            validity[i]['icon'] = html.I(className='icon checkmark green')
            validity[i]['message'] = validity[i]['messages']['positive']
            validity[i]['color'] = 'green'
        elif v.get('datagetter_metadata', {}).get(i)==False:
            validity[i]['class'] = 'positive'
            validity[i]['icon'] = html.I(className='icon close red')
            validity[i]['message'] = validity[i]['messages']['negative']
            validity[i]['color'] = 'red'

    file_type = v.get("datagetter_metadata", {}).get("file_type", "")
    file_type = FILE_TYPES.get(file_type.lower(), file_type)

    return html.Div(className='ui fluid card', children=[
        html.Div(className='content', children=[
            html.A(
                children=get_license_badge(v.get('license'), v.get("license_name")) + [' licence'], 
                href=v.get('license'), 
                target='_blank',
                className='ui basic label right floated',
                style={"position": "absolute !important", "left": 'calc(100% + 1rem) !important'}
            ),
            html.A(
                v.get("title"),
                href=v.get('distribution', [{}])[0].get('accessURL'),
                target="_blank",
                className='header'
            ),
            html.Div(className='meta', children=[
                html.Span(get_date_range(v)),
                html.Span('·'),
                html.Span(', '.join(
                    [babel.numbers.get_currency_name(k) for k in v.get("datagetter_aggregates", {}).get("currencies", {})]
                )),
                html.Span('·'),
                html.Span([
                    'Last modified ',
                    html.Time(dateTime=v.get("modified"), children=[
                    humanize.naturaldelta(
                        datetime.datetime.now() - dateutil.parser.parse(v.get("modified"), ignoretz=True)
                    )]),
                    ' ago'
                ]),
            ]),
            html.Div(className='description', children=[
                html.Div(className='ui small statistics', children=get_file_stats(v, as_statistic=True), 
                style={"margin-top": "24px"})
            ]),
        ]),
        html.Div(className='extra content', children=[
            html.Span(
                [
                    validity[i]['icon'],
                    validity[i]['message']
                ],
                className=validity[i]['class'],
                style={
                    "color": validity[i].get('color')
                }
            )
            for i in validity
        ], style={"padding": ".75em 1em"}),
        html.A(
            [
                html.I(className='download icon'),
                'Download from publisher (in {} format)'.format(file_type[0]),
            ],
            href=v.get('distribution', [{}])[0].get('downloadURL'),
            className='ui button ',
            title=file_type[1],
        ),
    ])


def get_file_stats(v, separator=None, as_statistic=True):
    stats = []
    agg = v.get("datagetter_aggregates")
    if agg is None:
        return stats

    def to_statistic(val, label):
        if as_statistic:
            return html.Span([
                html.Strong(val, className='value detail', style={}),
                html.Span(label, className='label'),
            ], className='statistic', style={})

        return html.Span([
            html.Strong(val, className='value detail', style={}),
            html.Span(label, className='label'),
        ], className='', style={})

    count = agg.get("count", 0)
    stats.append(to_statistic(
        humanize.intcomma(count), 
        pluralize("grant", count)
    ))

    recip = agg.get("distinct_recipient_org_identifier_count", 0)
    if recip > 0:
        stats.append(to_statistic(
            humanize.intcomma(recip),
            pluralize("recipient", recip),
        ))

    funders = agg.get("distinct_funding_org_identifier_count", 0)
    if funders > 1:
        stats.append(to_statistic(
            humanize.intcomma(funders),
            pluralize("funder", funders),
        ))
        

    if len(agg.get("currencies", {}))==1:
        for c in agg["currencies"]:
            cur = format_currency(agg["currencies"][c].get("total_amount", 0), c)
            stats.append(to_statistic(cur[0], cur[1]))
            

    if separator:
        result = [separator] * (len(stats) * 2 - 1)
        result[0::2] = stats
        return result
    
    return stats


def get_publisher_stats(pub_reg, **kwargs):
    data = {
        "count": 0,
        "currencies": {}
    }

    for r in pub_reg:
        data["count"] += r.get("datagetter_aggregates", {}).get("count", 0)
        for c, cagg in r.get("datagetter_aggregates", {}).get("currencies", {}).items():
            if c not in data["currencies"]:
                data["currencies"][c] = {"total_amount": 0}
            data["currencies"][c]["total_amount"] += cagg.get("total_amount", 0)

    return get_file_stats({"datagetter_aggregates": data}, **kwargs)

def get_date_range(v):
    agg = v.get("datagetter_aggregates")
    if agg is None:
        return None

    max_award_date = datetime.datetime.strptime(agg.get("max_award_date", None), "%Y-%m-%d")
    min_award_date = datetime.datetime.strptime(agg.get("min_award_date", None), "%Y-%m-%d")
    if max_award_date and min_award_date:
        min_award_ym = min_award_date.strftime("%b %Y")
        max_award_ym = max_award_date.strftime("%b %Y")
        if min_award_ym == max_award_ym:
            return max_award_ym
        else:
            return (min_award_ym + " to " + max_award_ym)

def get_license_badge(url, name):
    if "creativecommons.org/licenses" in url:
        components = ['cc'] + url.split("/")[-3].split("-")
        return [
            html.Img(src="https://mirrors.creativecommons.org/presskit/icons/{}.png".format(c.lower()), 
                title=name, style={'max-height': '24px', 'margin-right': '2px'})
            for c in components
        ]

    if "creativecommons.org/publicdomain" in url:
        components = ['publicdomain'] + url.split("/")[-3].split("-")
        return [
            html.Img(src="https://mirrors.creativecommons.org/presskit/icons/{}.png".format(c.lower()), 
                title=name, style={'max-height': '24px', 'margin-right': '2px'})
            for c in components
        ]

    if "creativecommons.org" in url:
        badge_url = url.replace("creativecommons.org/licenses", "i.creativecommons.org/l")
        badge_url = badge_url.replace("creativecommons.org/publicdomain", "i.creativecommons.org/p")
        badge_url = badge_url + "88x31.png"
        return [html.Img(src=badge_url, title=name, style={'max-height': '24px'})]

    if "open-government-licence" in url:
        badge_url = "http://www.nationalarchives.gov.uk/images/infoman/ogl-symbol-41px-retina-black.png"
        return [html.Img(src=badge_url, title=name, style={'max-height': '24px'})]

    if "http://www.opendefinition.org/licenses/odc-pddl" == url:
        return [html.Div('ODC PDDL', title=name, className='ui label')]
    
    return name