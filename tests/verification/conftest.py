import pytest
import hashlib
from app import create_app
from database import db as _db


@pytest.fixture(scope='function')
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def seed_user(app):
    """Standard user with API key for auth and cache tests."""
    from models.user import User
    with app.app_context():
        user = User(
            username='testuser',
            email='test@flock.test',
            password_hash=hashlib.md5(b'password').hexdigest(),
            api_key='test-api-key-abc123',
            is_active=True,
            is_admin=False
        )
        _db.session.add(user)
        _db.session.commit()
        _db.session.refresh(user)
        yield user


@pytest.fixture(scope='function')
def admin_user(app):
    """User with username 'admin' for admin route tests."""
    from models.user import User
    with app.app_context():
        user = User(
            username='admin',
            email='admin@flock.test',
            password_hash=hashlib.md5(b'admin123').hexdigest(),
            is_active=True,
            is_admin=True
        )
        _db.session.add(user)
        _db.session.commit()
        _db.session.refresh(user)
        yield user


@pytest.fixture(scope='function')
def regular_user(app):
    """Non-admin user for rejection tests."""
    from models.user import User
    with app.app_context():
        user = User(
            username='regularuser',
            email='regular@flock.test',
            password_hash=hashlib.md5(b'password').hexdigest(),
            is_active=True,
            is_admin=False
        )
        _db.session.add(user)
        _db.session.commit()
        _db.session.refresh(user)
        yield user


@pytest.fixture(scope='function')
def team_owner(app):
    """Team owner user for invitation tests."""
    from models.user import User
    from models.team import Team, TeamMember
    with app.app_context():
        owner = User(
            username='teamowner',
            email='owner@flock.test',
            password_hash=hashlib.md5(b'password').hexdigest(),
            is_active=True,
            is_admin=False
        )
        _db.session.add(owner)
        _db.session.flush()

        team = Team(
            name='Test Team',
            slug='test-team',
            owner_id=owner.id
        )
        _db.session.add(team)
        _db.session.flush()

        membership = TeamMember(
            team_id=team.id,
            user_id=owner.id,
            role='owner'
        )
        _db.session.add(membership)
        _db.session.commit()
        _db.session.refresh(owner)
        yield owner


@pytest.fixture(scope='function')
def invitee(app):
    """User to be invited in invitation tests."""
    from models.user import User
    with app.app_context():
        user = User(
            username='invitee',
            email='invitee@flock.test',
            password_hash=hashlib.md5(b'password').hexdigest(),
            is_active=True,
            is_admin=False
        )
        _db.session.add(user)
        _db.session.commit()
        _db.session.refresh(user)
        yield user
