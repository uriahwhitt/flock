"""
Verification: Trap 43 — Feature Flag Blueprint Context Collision

BROKEN state: When both 'projects' and 'messages' flags are True,
              the messages blueprint's before_request replaces
              g.current_user with a minimal dict that lacks is_admin
              and other User model fields. Code that accesses these
              fields fails silently (absorbed by except: pass).
FIXED state:  g.current_user provides consistent field access regardless
              of which blueprint flags are active. Admin-gated project
              actions work correctly when both flags are enabled.

FAIL-to-PASS tests:
  test_admin_field_accessible_with_both_flags

PASS-to-PASS tests:
  test_projects_loads_with_projects_flag_only
"""
import pytest
from unittest.mock import patch


def test_projects_loads_with_projects_flag_only(client, app, seed_user):
    """
    Projects list must load when only the projects flag is active.
    Baseline — must pass before and after any fix.
    """
    with client.session_transaction() as sess:
        sess['user'] = seed_user.username

    with patch('config.FEATURES', {'projects': True, 'messages': False,
                                    'hashtags': False, 'skills': False}):
        r = client.get('/projects')
    assert r.status_code == 200, \
        "Projects list failed with only projects flag active"


def test_projects_loads_with_both_flags(client, app, seed_user):
    """
    Projects list must return 200 when both projects and messages
    flags are active. On the broken implementation this may return
    200 but silently produce wrong data due to the context collision.
    """
    with client.session_transaction() as sess:
        sess['user'] = seed_user.username

    with patch('config.FEATURES', {'projects': True, 'messages': True,
                                    'hashtags': False, 'skills': False}):
        r = client.get('/projects')
    assert r.status_code == 200, \
        "Projects list failed with both flags active"


def test_admin_field_accessible_with_both_flags(client, app, admin_user):
    """
    When both flags are active, accessing g.current_user.is_admin must
    not raise AttributeError. On the broken implementation the messages
    blueprint replaces g.current_user with a dict — attribute access
    fails silently, and admin-conditional content is never rendered.

    A correct fix ensures consistent field access across blueprints.
    """
    with client.session_transaction() as sess:
        sess['user'] = 'admin'

    with patch('config.FEATURES', {'projects': True, 'messages': True,
                                    'hashtags': False, 'skills': False}):
        r = client.get('/projects')

    assert r.status_code == 200

    # The discriminating check: is_admin-gated content must be present.
    # If g.current_user.is_admin raised AttributeError silently,
    # admin nav or admin indicators will be absent from the response.
    has_admin_content = (
        b'admin' in r.data or
        b'Admin' in r.data or
        b'data-admin' in r.data
    )
    assert has_admin_content, (
        "Admin-conditional content absent from projects page when both "
        "flags active. g.current_user may not expose is_admin field "
        "when messages blueprint before_request has run."
    )
