import hashlib
import os
import json
import io
import datetime

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_resumable_upload

import pandas as pd
import babel.numbers
import humanize

from app import app
from load_data import get_registry_by_publisher
from charts import pluralize, format_currency

FILE_TYPES = {
    "xlsx": ("Excel", "Microsoft Excel"),
    "xls": ("Excel", "Microsoft Excel (pre 2007)"),
    "csv": ("CSV", "Comma Separated Values"),
    "json": ("JSON", "JSON is a structured file format"),
}

layout = html.Div(id="status-container", className='', children=[
    html.Table(className="ui padded table", children=[
        html.Thead([
            html.Tr([
                html.Th([]),
                html.Th('Publisher'),
                html.Th('Summary'),
                html.Th('Licence'),
                html.Th('Currencies'),
            ])
        ]),
        html.Tbody(id='status-rows', children=[])
    ])
])


@app.callback(Output('status-rows', 'children'),
              [Input('status-container', 'children')])
def update_status_container(_):
    print("update_status_container", _)
    reg = get_registry_by_publisher()
    rows = []
    for pub, pub_reg in reg.items():
        if len(pub_reg) == 1:
            rows.append(file_row(pub_reg[0], len(pub_reg)))
        else:
            rows.append(html.Tr([
                html.Td(
                    html.Img(
                        src=pub_reg[0].get("publisher", {}).get("logo"),
                        style={"max-width": '100px'}
                    ),
                    rowSpan=(len(pub_reg)+1)
                ),
                html.Td(
                    html.H3([
                        html.A(
                            pub_reg[0].get("publisher", {}).get("name"),
                            href=pub_reg[0].get("publisher", {}).get("website"),
                            target='_blank'
                        ),
                        html.Span("{} {}".format(len(pub_reg), pluralize("file", len(pub_reg))), className="ui label")
                    ], className="ui header"),
                    colSpan=4,
                    style={'padding-bottom': '0'}
                )
            ]))
            for v in pub_reg:
                rows.append(file_row(v, len(pub_reg)))
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

    return html.Tr(([
            html.Td(
                html.Img(
                    src=v.get("publisher", {}).get("logo"),
                    style={"max-width": '100px'}
                )
            )
        ] if files == 1 else []) + [
        html.Td([
                html.H3(([
                        html.A(
                            v.get("publisher", {}).get("name"),
                            href=v.get("publisher", {}).get("website"),
                            target='_blank'
                        ),
                        html.Br(),
                    ] if files == 1 else []) + [
                        html.Span(v.get("title"), className='sub header')
                    ], 
                    className="ui header"
                ),
                html.A(
                    'Publisher page',
                    href=v.get('distribution', [{}])[0].get('accessURL'),
                    target="_blank",
                    className='ui tiny primary basic button'
                ),
                html.A(
                    [
                        validity['downloads']['icon'],
                        'Download {}'.format(file_type[0]),
                    ],
                    href=v.get('distribution', [{}])[0].get('downloadURL'),
                    className='ui tiny basic button ' + validity['downloads']['class'],
                    title=file_type[1],
                ),
                html.Br(),
                html.Div(
                    [
                        html.Span(
                            [
                                validity[i]['icon'],
                                validity[i]['message']
                            ],
                            className=validity[i]['class'],
                            style={
                                "margin-right": "4px", 
                                "color": validity[i].get('color'),
                                "font-size": '90%'
                            }
                        )
                        for i in validity
                    ],
                    style={"margin-top": "8px"}
                )
                
            ], 
            style=style
        ),
        html.Td(
            html.Div(
                get_file_stats(v), 
                className='ui mini horizontal statistics'
            ),
            className='',
            style=style
        ),
        html.Td(
            html.A(
                children=get_license_badge(v.get('license'), v.get("license_name")), 
                href=v.get('license'), 
                target='_blank'
            ), 
            style=style
        ),
        html.Td(
            [
                html.Div(babel.numbers.get_currency_symbol(k), className='ui label') 
                for k, v in v.get("datagetter_aggregates", {}).get("currencies", {}).items()
            ], 
            style=style
        ),
    ])


def get_file_stats(v):
    stats = []
    agg = v.get("datagetter_aggregates")
    if agg is None:
        return stats

    def to_statistic(val, label):
        return html.Div([
            html.Strong(val, className='value detail', style={"min-width": "20px"}),
            html.Span(" " + label, className='label'),
        ], className='', style={"margin-bottom": "8px"})

    count = agg.get("count", 0)
    stats.append(to_statistic(
        humanize.intword(count), 
        pluralize("grant", count)
    ))

    recip = agg.get("distinct_recipient_org_identifier_count", 0)
    stats.append(to_statistic(
        humanize.intword(recip),
        pluralize("recipient", recip),
    ))

    funders = agg.get("distinct_funding_org_identifier_count", 0)
    if funders > 1:
        stats.append(to_statistic(
            humanize.intword(funders),
            pluralize("funder", funders),
        ))
        

    if len(agg.get("currencies", {}))==1:
        for c in agg["currencies"]:
            cur = format_currency(agg["currencies"][c].get("total_amount", 0), c)
            stats.append(to_statistic(cur[0], cur[1]))
            

    max_award_date = datetime.datetime.strptime(agg.get("max_award_date", None), "%Y-%m-%d")
    min_award_date = datetime.datetime.strptime(agg.get("min_award_date", None), "%Y-%m-%d")
    if max_award_date and min_award_date:
        min_award_ym = min_award_date.strftime("%b %Y")
        max_award_ym = max_award_date.strftime("%b %Y")
        if min_award_ym == max_award_ym:
            stats.append(max_award_ym)
        else:
            stats.append(min_award_ym + " to " + max_award_ym)

    return stats


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
        return html.Img(src=badge_url, title=name, style={'max-height': '24px'})

    if "open-government-licence" in url:
        badge_url = "http://www.nationalarchives.gov.uk/images/infoman/ogl-symbol-41px-retina-black.png"
        return html.Img(src=badge_url, title=name, style={'max-height': '24px'})

    if "http://www.opendefinition.org/licenses/odc-pddl" == url:
        return html.Div('ODC PDDL', title=name, className='ui label')
    
    return name