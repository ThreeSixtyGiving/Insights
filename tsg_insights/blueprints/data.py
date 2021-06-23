import datetime
import io

import pandas as pd
from flask import Blueprint, Response, abort
from flask import current_app as app
from flask import jsonify, render_template, request

from tsg_insights_dash.data.filters import get_filtered_df
from tsg_insights_dash.data.results import CHARTS, get_statistics

from ..data.utils import format_currency

bp = Blueprint("data", __name__)


@bp.route("/map/<fileid>")
def create_grants_map(fileid):

    df = get_filtered_df(fileid, **dict(request.args.lists()))

    if df is None:
        abort(404)

    df.dropna(subset=["__geo_lat", "__geo_long"])
    df.loc[:, "__geo_lat"] = df["__geo_lat"].astype(float)
    df.loc[:, "__geo_long"] = df["__geo_long"].astype(float)
    df.loc[:, "Amount String"] = df.apply(
        lambda x: format_currency(x["Amount Awarded"], x["Currency"], humanize_=False)[
            0
        ],
        axis=1,
    )
    df.loc[:, "Award Date"] = df["Award Date"].dt.strftime("%d %B %Y")

    geo = (
        df[
            [
                "__geo_lat",
                "__geo_long",
                "Recipient Org:0:Name",
                "Funding Org:0:Name",
                "Amount Awarded",
                "Currency",
                "Amount String",
                "Award Date",
            ]
        ]
        .dropna()
        .to_dict("index")
    )

    return render_template(
        "map.html.j2",
        geo=geo,
        mapbox_access_token=app.config.get("MAPBOX_ACCESS_TOKEN"),
        mapbox_style=app.config.get("MAPBOX_STYLE"),
        current_year=datetime.datetime.now().year,
    )


@bp.route("/<fileid>.geojson")
def fetch_file_geojson(fileid):

    # @TODO: fetch filters
    df = get_filtered_df(fileid, **dict(request.args.lists()))

    popup_col = "Recipient Org:0:Name"
    if popup_col not in df.columns and "Recipient Org:0:Identifier" in df.columns:
        popup_col = "Recipient Org:0:Identifier"

    geo = df[["__geo_lat", "__geo_long", popup_col]].dropna()
    geo = (
        geo.groupby(["__geo_lat", "__geo_long", popup_col])
        .size()
        .rename("grants")
        .reset_index()
    )

    return jsonify(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [g["__geo_lat"], g["__geo_long"]],
                    },
                    "properties": {
                        "name": g[popup_col],
                        "grants": g["grants"],
                    },
                }
                for k, g in geo.iterrows()
            ],
        }
    )


@bp.route("/<fileid>")
def fetch_file(fileid):

    # @TODO: fetch filters
    df = get_filtered_df(fileid, **request.form.get("filters", {}))

    results = {
        chart_id: chart_def["get_results"](df) for chart_id, chart_def in CHARTS.items()
    }
    results["statistics"] = get_statistics(df)
    return jsonify(results)


@bp.route("/download/<fileid>.<format>")
def download_file(fileid, format):
    df = get_filtered_df(fileid)

    fields_to_exclude = [
        "Recipient Org:0:Identifier:Scheme",
        "Recipient Org:0:Identifier:Clean",
        "__org_orgid",
        "__org_charity_number",
        "__org_company_number",
        # '__geo_ctry',
        # '__geo_cty',
        # '__geo_laua',
        # '__geo_pcon',
        # '__geo_rgn',
        "__geo_imd",
        "__geo_ru11ind",
        "__geo_oac11",
        # '__geo_lat',
        # '__geo_long',
    ]

    column_renames = {
        "__org_date_registered": "Insights:Recipient Org:Date Registered",
        "__org_date_removed": "Insights:Recipient Org:Date Removed",
        "__org_latest_income": "Insights:Recipient Org:Latest Income",
        "__org_latest_income_bands": "Insights:Recipient Org:Latest Income:Bands",
        "__org_org_type": "Insights:Recipient Org:Organisation Type",
        "__org_postcode": "Insights:Recipient Org:Postcode",
        "__org_age": "Insights:Recipient Org:Age:Days",
        "__org_age_bands": "Insights:Recipient Org:Age:Bands",
        "__geo_ctry": "Insights:Geo:Country",
        "__geo_cty": "Insights:Geo:County",
        "__geo_laua": "Insights:Geo:Local Authority",
        "__geo_pcon": "Insights:Geo:Parliamentary Constituency",
        "__geo_rgn": "Insights:Geo:Region",
        "__geo_lat": "Insights:Geo:Latitude",
        "__geo_long": "Insights:Geo:Longitude",
        "Award Date:Year": "Insights:Award Date:Year",
        "Amount Awarded:Bands": "Insights:Amount Awarded:Bands",
    }

    if df is not None:

        columns = [c for c in df.columns if c not in fields_to_exclude]
        df = df[columns].rename(columns=column_renames)

        if format == "csv":
            csvdata = df.to_csv(index=False)
            return Response(
                csvdata,
                mimetype="text/csv",
                headers={
                    "Content-disposition": "attachment; filename={}.csv".format(fileid)
                },
            )
        elif format == "xlsx":
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine="xlsxwriter")
            for col in df.select_dtypes(["datetimetz"]).columns:
                df[col] = df[col].astype(str).str[:-6]
            csvdata = df.to_excel(writer, sheet_name="grants", index=False)
            writer.save()
            return Response(
                output.getvalue(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-disposition": "attachment; filename={}.xlsx".format(fileid)
                },
            )
        elif format == "json":
            pass
        abort(400)
    abort(404)
