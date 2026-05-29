import pytest
from app import create_app
from database import db as _db


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        with app.app_context():
            _db.create_all()
            yield client
            _db.drop_all()
    # Note: _cache and _pending_notifications are NOT reset between tests


@pytest.fixture
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()
