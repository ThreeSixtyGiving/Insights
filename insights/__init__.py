import os

from flask import Flask, abort, render_template, url_for
from flask_graphql import GraphQLView

from insights import settings
from insights.commands import fetch_data
from insights.data import get_frontpage_options, get_funder_names
from insights.db import GeoName, Publisher, db, migrate
from insights.schema import schema
from insights.utils import list_to_string

__version__ = "0.1.0"


def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_mapping(
        DATASTORE_URL=os.environ.get("DATASTORE_URL"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DB_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAPBOX_ACCESS_TOKEN=os.environ.get("MAPBOX_ACCESS_TOKEN"),
    )

    db.init_app(app)
    migrate.init_app(app, db)

    app.cli.add_command(fetch_data.cli)

    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view(
            "graphql", schema=schema, graphiql=True  # for having the GraphiQL interface
        ),
    )

    @app.context_processor
    def inject_nav():
        return dict(
            nav={
                "360Insights": url_for("index"),
                "About": url_for("about"),
                "GrantNav": "https://grantnav.threesixtygiving.org/",
            }
        )

    @app.route("/")
    def index():
        return render_template("index.html.j2", dataset_select=get_frontpage_options())

    @app.route("/about")
    def about():
        return render_template("about.html.j2")

    def data_template(
        filters,
        dataset=settings.DEFAULT_DATASET,
        title="Granty grants",
        subtitle="Grants made by",
        template="data.html.j2",
    ):
        return render_template(
            template,
            dataset=dataset,
            base_filters=filters,
            bin_labels={
                "byAmountAwarded": settings.AMOUNT_BIN_LABELS,
                "byOrgAge": settings.AGE_BIN_LABELS,
                "byOrgSize": settings.INCOME_BIN_LABELS,
            },
            title=title,
            subtitle=subtitle,
        )

    @app.route("/data")
    @app.route("/data/<dataset>")
    @app.route("/<data_type>/<data_id>")
    @app.route("/<data_type>/<data_id>/<page>")
    def data(
        data_type="data", page="data", dataset=settings.DEFAULT_DATASET, data_id=None
    ):
        if data_type not in (
            "data",
            "funder",
            "funder_type",
            "publisher",
            "file",
            "area",
        ):
            abort(404, "Page not found")
        if page not in ("data", "map"):
            abort(404, "Page not found")

        filters = {}
        title = (
            "360Giving publishers" if dataset == settings.DEFAULT_DATASET else dataset
        )
        subtitle = "Grants made by"

        if data_type == "funder":
            funders = data_id.split("+")
            all_funder_names = get_funder_names(settings.DEFAULT_DATASET)
            funder_names = [
                all_funder_names[f] for f in funders if f in all_funder_names
            ]
            if len(funder_names) != len(funders):
                abort(404, description="Funder not found")
            filters["funders"] = funders
            title = (
                list_to_string(funder_names)
                if len(funder_names) < 8
                else "{:,.0f} funders".format(len(funder_names))
            )

        elif data_type == "funder_type":
            funder_types = data_id.split("+")
            filters["funderTypes"] = funder_types
            title = list_to_string(funder_types)

        elif data_type == "publisher":
            publishers = data_id.split("+")
            publisher_names = []
            for p in publishers:
                publisher = db.session.query(Publisher).filter_by(prefix=p).first()
                if not publisher:
                    abort(404, "Publisher {} not found".format(p))
                publisher_names.append(publisher.name)
            filters["publishers"] = publishers
            title = list_to_string(publisher_names)
            subtitle = "Grants published by"

        elif data_type == "file":
            filters["files"] = data_id.split("+")

        elif data_type == "area":
            areas = data_id.split("+")
            area_names = []
            for a in areas:
                area = db.session.query(GeoName).filter_by(id=a).first()
                if not area:
                    abort(404, "Area {} not found".format(a))
                area_names.append(area.name)
            filters["area"] = areas
            title = list_to_string(area_names)
            subtitle = "Grants made in"

        if page == "map":
            template = "map.html.j2"
        else:
            template = "data.html.j2"

        return data_template(
            filters,
            dataset=dataset,
            title=title,
            subtitle=subtitle,
            template=template,
        )

    return app
