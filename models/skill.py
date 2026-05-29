from datetime import datetime
from database import db


class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)

    user = db.relationship('User', backref='skills')


class Endorsement(db.Model):
    __tablename__ = 'endorsements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    endorser_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endorsed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skill = db.relationship('Skill', backref='endorsements')
    endorser = db.relationship('User', foreign_keys=[endorser_id], backref='given_endorsements')
    endorsed = db.relationship('User', foreign_keys=[endorsed_id], backref='received_endorsements')
