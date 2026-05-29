import pytest
from database import db
from models.user import User


def register_user(client, username='testuser', email='test@example.com',
                  password='testpass', display_name='Test User'):
    return client.post('/register', data={
        'username': username,
        'email': email,
        'password': password,
        'display_name': display_name
    }, follow_redirects=False)


def login_user(client, username='testuser', password='testpass'):
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=False)


def test_register(client):
    resp = register_user(client)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/feed')


def test_register_creates_user(client, app):
    register_user(client)
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'


def test_register_duplicate_username(client):
    register_user(client)
    resp = register_user(client)
    assert b'already taken' in resp.data


def test_login_success(client):
    register_user(client)
    resp = login_user(client)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/feed')


def test_login_wrong_password(client):
    register_user(client)
    resp = login_user(client, password='wrongpass')
    assert b'Invalid' in resp.data


def test_login_unknown_user(client):
    resp = login_user(client, username='nobody')
    assert b'Invalid' in resp.data


def test_logout(client):
    register_user(client)
    login_user(client)
    resp = client.get('/logout', follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')
