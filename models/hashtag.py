from datetime import datetime
from database import db


class Hashtag(db.Model):
    __tablename__ = 'hashtags'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag = db.Column(db.String(80), unique=True, nullable=False)
    post_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PostHashtag(db.Model):
    __tablename__ = 'post_hashtags'

    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)
    hashtag_id = db.Column(db.Integer, db.ForeignKey('hashtags.id'), primary_key=True)

    post = db.relationship('Post', backref='hashtag_assocs')
    hashtag = db.relationship('Hashtag', backref='post_assocs')
