import pytest
from database import db
from models.user import User
from models.post import Post


def register_and_login(client, username='testuser', password='testpass'):
    client.post('/register', data={
        'username': username,
        'email': f'{username}@example.com',
        'password': password,
        'display_name': username.title()
    })
    client.post('/login', data={'username': username, 'password': password})


def test_feed_requires_login(client):
    resp = client.get('/feed', follow_redirects=False)
    assert resp.status_code == 302


def test_feed_loads(client):
    register_and_login(client)
    resp = client.get('/feed')
    assert resp.status_code == 200
    assert b'Share something' in resp.data


def test_create_post(client, app):
    register_and_login(client)
    resp = client.post('/feed/post', data={'content': 'Hello world'}, follow_redirects=False)
    assert resp.status_code == 302

    with app.app_context():
        post = Post.query.filter_by(content='Hello world').first()
        assert post is not None


def test_post_appears_in_feed(client):
    register_and_login(client)
    client.post('/feed/post', data={'content': 'Test post content'})
    resp = client.get('/feed')
    assert b'Test post content' in resp.data


def test_post_detail(client, app):
    register_and_login(client)
    client.post('/feed/post', data={'content': 'Detail test'})
    with app.app_context():
        post = Post.query.filter_by(content='Detail test').first()
        post_id = post.id
    resp = client.get(f'/feed/post/{post_id}')
    assert resp.status_code == 200
    assert b'Detail test' in resp.data


def test_like_post(client, app):
    register_and_login(client)
    client.post('/feed/post', data={'content': 'Like me'})
    with app.app_context():
        post = Post.query.filter_by(content='Like me').first()
        post_id = post.id
    import json
    resp = client.post(f'/feed/post/{post_id}/like',
                       data=json.dumps({}),
                       content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['liked'] is True
    assert data['like_count'] == 1


def test_delete_post(client, app):
    register_and_login(client)
    client.post('/feed/post', data={'content': 'Delete me'})
    with app.app_context():
        post = Post.query.filter_by(content='Delete me').first()
        post_id = post.id
    resp = client.post(f'/feed/post/{post_id}/delete', follow_redirects=False)
    assert resp.status_code == 302
    with app.app_context():
        post = Post.query.get(post_id)
        assert post.is_deleted is True
