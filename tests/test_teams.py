import pytest
import json
from database import db
from models.team import Team


def register_and_login(client, username='testuser', password='testpass'):
    client.post('/register', data={
        'username': username,
        'email': f'{username}@example.com',
        'password': password,
        'display_name': username.title()
    })
    client.post('/login', data={'username': username, 'password': password})


def test_teams_list(client):
    resp = client.get('/teams')
    assert resp.status_code == 200


def test_create_team(client, app):
    register_and_login(client)
    resp = client.post('/teams/create', data={
        'name': 'Test Team',
        'slug': 'test-team',
        'description': 'A test team',
        'is_public': 'true'
    }, follow_redirects=False)
    assert resp.status_code == 302

    with app.app_context():
        team = Team.query.filter_by(slug='test-team').first()
        assert team is not None
        assert team.member_count == 1


def test_team_detail(client):
    register_and_login(client)
    client.post('/teams/create', data={
        'name': 'My Team',
        'slug': 'my-team',
        'description': 'desc',
        'is_public': 'true'
    })
    resp = client.get('/teams/my-team')
    assert resp.status_code == 200
    assert b'My Team' in resp.data


def test_join_team(client, app):
    register_and_login(client, 'owner', 'pass')
    client.post('/teams/create', data={
        'name': 'Join Test',
        'slug': 'join-test',
        'description': '',
        'is_public': 'true'
    })
    client.get('/logout')
    register_and_login(client, 'joiner', 'pass')

    formData = b'slug=join-test'
    resp = client.post('/teams/join-test/join',
                       data=formData,
                       content_type='application/x-www-form-urlencoded')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['member'] is True


def test_create_team_requires_login(client):
    resp = client.get('/teams/create', follow_redirects=False)
    assert resp.status_code == 302
