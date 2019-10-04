from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_caching import CachingQuery
from flask_caching import Cache
from flask_migrate import Migrate

db = SQLAlchemy(query_class=CachingQuery)
cache = Cache()
migrate = Migrate(compare_type=True)
