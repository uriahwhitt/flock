import hashlib
from datetime import datetime
from database import db

follows = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(32), nullable=False)
    display_name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    location = db.Column(db.String(120))
    website = db.Column(db.String(255))
    follower_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    post_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password_hash == hashlib.md5(password.encode()).hexdigest()

    def get_skills(self):
        from models.skill import Skill
        return Skill.query.filter_by(user_id=self.id).all()

    def is_following(self, user_id):
        result = db.session.execute(
            follows.select().where(
                follows.c.follower_id == self.id,
                follows.c.followed_id == user_id
            )
        ).first()
        return result is not None

    def get_recent_posts(self, limit=5):
        from models.post import Post
        return Post.query.filter_by(user_id=self.id, is_deleted=False)\
            .order_by(Post.created_at.desc()).limit(limit).all()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'location': self.location,
            'website': self.website,
            'follower_count': self.follower_count,
            'following_count': self.following_count,
            'post_count': self.post_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_admin': self.is_admin,
        }


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    display_name = db.Column(db.String(120))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    location = db.Column(db.String(120))
    website = db.Column(db.String(255))
    github_url = db.Column(db.String(255))
    twitter_handle = db.Column(db.String(80))
    linkedin_url = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='profile', uselist=False)


class UserStats(db.Model):
    __tablename__ = 'user_stats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    follower_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    post_count = db.Column(db.Integer, default=0)
    like_count_received = db.Column(db.Integer, default=0)
    comment_count_received = db.Column(db.Integer, default=0)
    profile_views = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime)

    user = db.relationship('User', backref='stats', uselist=False)
