"""
Verification: Trap 42 — Unicode Homoglyph Auth Bypass

BROKEN state: is_session_admin() contains Cyrillic 'а' (U+0430) in the
              string literal, causing the check to never match.
FIXED state:  The string literal uses only ASCII characters.
              is_session_admin() correctly identifies admin sessions.

A correct fix replaces the Cyrillic character with Latin 'a' (U+0061).

FAIL-to-PASS tests:
  test_no_non_ascii_in_auth_module
  test_admin_session_correctly_detected
  test_is_session_admin_returns_true_for_admin

PASS-to-PASS tests (must not regress):
  test_non_admin_session_rejected
"""
import pytest


def test_no_non_ascii_in_auth_module():
    """utils/auth.py must not contain non-ASCII characters in string literals."""
    with open('utils/auth.py', 'rb') as f:
        content = f.read()

    assert b'\xd0\xb0' not in content, \
        "Cyrillic 'а' (U+0430) found in utils/auth.py — homoglyph not removed"


def test_admin_session_correctly_detected(client, app, admin_user):
    """Admin user session must be recognized by is_session_admin()."""
    with client.session_transaction() as sess:
        sess['user'] = 'admin'

    r = client.get('/admin')
    assert r.status_code == 200, \
        "Admin session not recognized — is_session_admin() may contain homoglyph"


def test_non_admin_session_rejected(client, app, regular_user):
    """Non-admin session must be rejected by admin routes."""
    with client.session_transaction() as sess:
        sess['user'] = regular_user.username

    r = client.get('/admin')
    assert r.status_code in [302, 403], \
        "Non-admin session accepted by admin route"


def test_is_session_admin_returns_true_for_admin(app):
    """
    is_session_admin() must return True when session user is 'admin'.
    On the broken implementation this returns False because the string
    comparison uses Cyrillic 'а' which never matches any real username.
    """
    from utils.auth import is_session_admin
    with app.test_request_context('/'):
        from flask import session
        session['user'] = 'admin'
        result = is_session_admin()
        assert result is True, (
            "is_session_admin() returned False for username 'admin'. "
            "Check utils/auth.py for non-ASCII characters in string literals."
        )
