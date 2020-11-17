import datetime
import os
import tempfile

import pytest

from insights import __version__, create_app
from insights.db import Grant, Publisher, SourceFile, db


def test_version():
    assert __version__ == "0.1.0"


@pytest.fixture
def test_app():
    app = create_app()
    db_fd, db_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{}".format(db_path)
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        create_dummy_grants()
        yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client():
    app = create_app()
    db_fd, db_path = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{}".format(db_path)
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            create_dummy_grants()
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def create_dummy_grants():
    publisher = Publisher(prefix="360G-pub", name="Publisher")
    db.session.merge(publisher)
    source_file = SourceFile(
        id="12345",
        title="Source file",
        publisher=publisher,
    )
    db.session.merge(source_file)
    for i in range(0, 10):
        g = Grant(
            dataset="main",
            grant_id=f"dummy_{i}",
            title=f"Dummy Grant {i}",
            description="A dummy grant",
            currency="GBP",
            amountAwarded=100 * (i + 1),
            awardDate=datetime.date(2020, (i % 12) + 1, (i % 28) + 1),
            recipientOrganization_id=f"360G-dummy-{i}",
            recipientOrganization_name=f"Dummy Recipient {i}",
            fundingOrganization_id=f"360G-dummy-funder-{i % 3}",
            fundingOrganization_name=f"Dummy Funder {i % 3}",
            publisher=publisher,
            source_file=source_file,
        )
        db.session.merge(g)
    db.session.commit()


def test_index(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"See your grantmaking in new ways" in rv.data
    assert b"Dummy Funder 0" in rv.data
    assert b"https://grantnav.threesixtygiving.org/" in rv.data


def test_about(client):
    rv = client.get("/about")
    assert rv.status_code == 200
    assert b"About 360Insights" in rv.data


def test_funder_dash(client):
    rv = client.get("/funder/360G-dummy-funder-0")
    assert rv.status_code == 200
    assert b"360G-dummy-funder-0" in rv.data


def test_funder_dash_404(client):
    rv = client.get("/funder/360G-dummy-funder-not-found")
    assert rv.status_code == 404


def test_publisher_dash(client):
    rv = client.get("/publisher/360G-pub")
    assert rv.status_code == 200
    assert b"360G-pub" in rv.data


def test_publisher_dash_404(client):
    rv = client.get("/publisher/360G-dummy-pub-not-found")
    assert rv.status_code == 404
