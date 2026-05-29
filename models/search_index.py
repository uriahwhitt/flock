from datetime import datetime
from database import db


class SearchIndex(db.Model):
    __tablename__ = 'search_index'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_type = db.Column(db.String(20), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    searchable_text = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
