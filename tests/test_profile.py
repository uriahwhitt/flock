import pytest
import json
from database import db
from models.user import User


def register_and_login(client, username='testuser', password='testpass'):
    client.post('/register', data={
        'username': username,
        'email': f'{username}@example.com',
        'password': password,
        'display_name': username.title()
    })
    client.post('/login', data={'username': username, 'password': password})


def test_view_profile(client):
    register_and_login(client)
    resp = client.get('/profile/testuser')
    assert resp.status_code == 200
    assert b'testuser' in resp.data


def test_edit_profile_page(client):
    register_and_login(client)
    resp = client.get('/profile/edit')
    assert resp.status_code == 200


def test_edit_profile_update(client, app):
    register_and_login(client)
    resp = client.post('/profile/edit', data={
        'display_name': 'Updated Name',
        'bio': 'My bio',
        'location': 'NYC',
        'website': ''
    }, follow_redirects=False)
    assert resp.status_code == 302

    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user.display_name == 'Updated Name'
        assert user.bio == 'My bio'


def test_follow_user(client, app):
    register_and_login(client, 'user1', 'pass1')
    client.get('/logout')
    register_and_login(client, 'user2', 'pass2')
    client.get('/logout')
    register_and_login(client, 'user1', 'pass1')

    resp = client.post('/profile/user2/follow',
                       data=json.dumps({}),
                       content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['following'] is True
    assert data['follower_count'] == 1


def test_profile_requires_existing_user(client):
    resp = client.get('/profile/nonexistent')
    assert resp.status_code == 404
