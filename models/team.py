from datetime import datetime
from database import db


class TeamMember(db.Model):
    __tablename__ = 'team_members'

    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role = db.Column(db.String(20), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='team_memberships')
    team = db.relationship('Team', backref='members')


class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    member_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', backref='owned_teams')

    def get_members(self):
        from models.user import User
        return User.query.join(TeamMember, TeamMember.user_id == User.id)\
            .filter(TeamMember.team_id == self.id).all()

    def is_member(self, user_id):
        return TeamMember.query.filter_by(team_id=self.id, user_id=user_id).first() is not None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'avatar_url': self.avatar_url,
            'member_count': self.member_count,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'owner': {
                'id': self.owner.id,
                'username': self.owner.username,
                'display_name': self.owner.display_name,
            } if self.owner else None,
        }


class TeamRole(db.Model):
    __tablename__ = 'team_roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member')
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship('Team', backref='roles')
    user = db.relationship('User', foreign_keys=[user_id], backref='team_roles')
    granter = db.relationship('User', foreign_keys=[granted_by])


class TeamInvitation(db.Model):
    """Represents an invitation to join a team.

    Manages the full lifecycle of a team invitation from creation through
    acceptance, revocation, or expiration. State transitions are:
        PENDING  -> ACCEPTED (invitee accepts the invitation)
        PENDING  -> REVOKED  (admin cancels before acceptance)
        PENDING  -> EXPIRED  (TTL passes without action)

    The role field is set by the inviting admin at creation time and
    determines what role the invitee receives upon acceptance.
    """
    __tablename__ = 'team_invitations'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    invited_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    invited_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(20), default='member')
    state = db.Column(db.String(20), default='PENDING')
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
