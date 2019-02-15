from flask import Blueprint, jsonify, request

from tsg_insights_dash.data.filters import get_filtered_df
from tsg_insights_dash.data.results import get_statistics, CHARTS

bp = Blueprint('data', __name__)


@bp.route('/<fileid>.geojson')
def fetch_file_geojson(fileid):

    # @TODO: fetch filters
    df = get_filtered_df(fileid, **request.form.get("filters", {}))

    popup_col = 'Recipient Org:0:Name'
    if popup_col not in df.columns and 'Recipient Org:0:Identifier' in df.columns:
        popup_col = 'Recipient Org:0:Identifier'

    geo = df[["__geo_lat", "__geo_long", popup_col]].dropna()
    geo = geo.groupby(["__geo_lat", "__geo_long", popup_col]
                      ).size().rename("grants").reset_index()

    return jsonify({
        "FeatureCollection": {
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [g["__geo_lat"], g["__geo_long"]]
                    },
                    "properties": {
                        "name": g[popup_col],
                        "grants": g['grants'],
                    }
                }
                for k, g in geo.iterrows()
            ]
        }
    })

            


@bp.route('/<fileid>')
def fetch_file(fileid):

    # @TODO: fetch filters
    df = get_filtered_df(fileid, **request.form.get("filters", {}))

    results = {
        chart_id: chart_def['get_results'](df)
        for chart_id, chart_def in CHARTS.items()
    }
    results['statistics'] = get_statistics(df)
    return jsonify(results)


@bp.route('/download/<fileid>.<format>')
def download_file(fileid, format):
    df = get_filtered_df(fileid)
    if df is not None:
        if format == "csv":
            csvdata = df.to_csv(index=False)
            return flask.Response(
                csvdata,
                mimetype="text/csv",
                headers={"Content-disposition":
                         "attachment; filename={}.csv".format(fileid)})
        elif format == 'xlsx':
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            csvdata = df.to_excel(writer, sheet_name='grants', index=False)
            writer.save()
            return flask.Response(
                output.getvalue(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-disposition":
                         "attachment; filename={}.xlsx".format(fileid)})
        elif format == "json":
            pass
        flask.abort(400)
    flask.abort(404)
