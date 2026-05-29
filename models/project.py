from datetime import datetime
from database import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    repo_url = db.Column(db.String(255))
    live_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', backref='projects')
    team = db.relationship('Team', backref='projects')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'repo_url': self.repo_url,
            'live_url': self.live_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'owner': {
                'id': self.owner.id,
                'username': self.owner.username,
                'display_name': self.owner.display_name,
            } if self.owner else None,
            'team': {
                'id': self.team.id,
                'name': self.team.name,
                'slug': self.team.slug,
            } if self.team else None,
        }


class ProjectContributor(db.Model):
    __tablename__ = 'project_contributors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='contributor')
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', backref='contributors')
    user = db.relationship('User', backref='project_contributions')
