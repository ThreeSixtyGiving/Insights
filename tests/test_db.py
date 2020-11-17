from insights.db import Grant

from .test_insights import test_app


def test_grant_str(test_app):
    with test_app.app_context():
        g = Grant.query.first()
        assert str(g) == "<Grant 1>"
