import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly.graph_objs as go
import inflect
import humanize


DEFAULT_TABLE_FIELDS = ["Title", "Description", "Amount Awarded", 
                        "Award Date", "Recipient Org:Name", 
                        "Grant Programme:Title"]


def get_bar_data(values, name="Grants", chart_type='bar'):
    titles = [i[0] for i in values.iteritems()]
    titles = [" - ".join(get_unique_list(i)) if isinstance(i, (list, tuple)) else i for i in titles]
    bar_data = {
        'x': titles, 
        'y': [i[1] for i in values.iteritems()], 
        'type': chart_type, 
        'name': 'Grants'
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
    return dcc.Graph(
        id="grant_programme_chart",
        figure={
            'data': [get_bar_data(df["Grant Programme:Title"].value_counts())],
            'layout': {
                'title': 'Grant programmes (number of grants)'
            }
        }
    )

def amount_awarded_chart(df):
    return dcc.Graph(
        id="amount_awarded_chart",
        figure={
            'data': [get_bar_data(df["Amount Awarded:Bands"].value_counts().sort_index())],
            'layout': {
                'title': 'Amount awarded (number of grants)'
            }
        }
    )

def awards_over_time_chart(df):
    return dcc.Graph(
        id="awards_over_time_chart",
        figure={
            'data': [get_bar_data(df["Award Date"].apply(lambda x: x.strftime("%Y-%m")).value_counts().sort_index())],
            'layout': {
                'title': 'Award Date (number of grants)'
            }
        } 
    )

def region_and_country_chart(df):
    values = df.fillna({"__geo_ctry": "Unknown", "__geo_rgn": "Unknown"}).groupby(["__geo_ctry", "__geo_rgn"]).agg({
        "Amount Awarded": "sum",
        "Title": "size"
    })
    return dcc.Graph(
        id="region_and_country_chart",
        figure={
            'data': [get_bar_data(values["Title"], chart_type='column')],
            'layout': {
                'title': 'Region and Country (number of grants)'
            }
        } 
    )

def organisation_type_chart(df):
    values = df["__org_org_type"].fillna("Unknown").value_counts().sort_index()
    return dcc.Graph(
        id="organisation_type_chart",
        figure={
            "data": [go.Pie(
                labels=[i[0] for i in values.iteritems()],
                values=[i[1] for i in values.iteritems()],
                hole=0.4,
                )],
            'layout': {
                'title': 'Recipient type (number of grants)'
            }
        }
    )

def organisation_income_chart(df):
    return dcc.Graph(
        id="organisation_income_chart",
        figure={
            'data': [get_bar_data(df["__org_latest_income_bands"].value_counts().sort_index())],
            'layout': {
                'title': 'Latest income of charity recipients (number of grants)'
            }
        } 
    )

def organisation_age_chart(df):
    return dcc.Graph(
        id="organisation_age_chart",
        figure={
            'data': [get_bar_data(df["__org_age_bands"].value_counts().sort_index())],
            'layout': {
                'title': 'Age of charity recipients (number of grants)'
            }
        } 
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
    amount_awarded = df["Amount Awarded"].sum()
    amount_awarded_str = humanize.intword(amount_awarded).split(" ")
    if len(amount_awarded_str) == 1:
        amount_awarded_str = [humanize.intcomma(amount_awarded), ""]
    return html.Div(
        className='ui statistics',
        children=[
            html.Div(className='statistic', children=[
                html.Div(className='value', children="{:,.0f}".format(len(df))),
                html.Div(className='label', children=pluralize("grant", len(df)))
            ]),
            html.Div(className='statistic', children=[
                html.Div(className='value', children="{:,.0f}".format(df["Recipient Org:Identifier"].unique().size)),
                html.Div(className='label', children=pluralize("recipient", df["Recipient Org:Identifier"].unique().size))
            ]),
            html.Div(className='statistic', children=[
                html.Div(className='value', children="£{}".format(amount_awarded_str[0])),
                html.Div(className='label', children=amount_awarded_str[1])
            ]),
        ]
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

    return_str = "{} made by {} {}".format(pluralize("Grant", len(df)), funders, years)

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