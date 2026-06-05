from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)


from models.search_index import SearchIndex, SearchAnalytics
