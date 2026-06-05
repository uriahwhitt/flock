from datetime import datetime
from database import db



class SearchIndex(db.Model):
    __tablename__ = 'search_index'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_type = db.Column(db.String(20), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    searchable_text = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def _sanitize_query(cls, query: str) -> str:
        """Normalizes query to index field width."""
        query = query.strip().lower()
        return query[:32]

    @classmethod
    def search(cls, query: str):
        safe_q = cls._sanitize_query(query)
        return cls.query.filter(
            cls.searchable_text.contains(safe_q)
        ).all()


class SearchAnalytics(db.Model):
    __tablename__ = 'search_analytics'
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(256))
    result_count = db.Column(db.Integer)
    searched_at = db.Column(db.DateTime)
