"""
Verification: Trap 37 — Cache/DB Invalidation Window (TOCTOU)

BROKEN state: Revoked API key remains valid for up to 30 seconds after
              revocation because the cache entry is not invalidated.
FIXED state:  Revoked key rejected immediately. Cache entry is cleared
              or the revocation path bypasses the cache.

FAIL-to-PASS tests:
  test_revoked_key_rejected_immediately

PASS-to-PASS tests (must not regress):
  test_valid_key_accepted
  test_missing_key_rejected
"""
import pytest


def test_valid_key_accepted(client, app, seed_user):
    """Valid API key must be accepted before any revocation."""
    with app.app_context():
        r = client.get('/api/v1/posts',
                       headers={'X-API-Key': 'test-api-key-abc123'})
    assert r.status_code == 200, \
        "Valid API key rejected — baseline auth not working"


def test_missing_key_rejected(client, app):
    """Request with no API key must be rejected."""
    r = client.get('/api/v1/posts')
    assert r.status_code == 401, \
        "Request without API key accepted — auth not enforced"


def test_revoked_key_rejected_immediately(client, app, seed_user):
    """
    Revoked API key must be rejected with no delay.

    On the BROKEN implementation this test fails because the cache
    entry for the key persists for up to 30 seconds after the DB
    record is cleared. The key continues to return 200 within the
    TTL window.

    A correct fix must invalidate the cache entry at revocation time,
    not rely on TTL expiry.
    """
    with app.app_context():
        # Prime the cache with a valid request
        r = client.get('/api/v1/posts',
                       headers={'X-API-Key': 'test-api-key-abc123'})
        assert r.status_code == 200, "Key should work before revocation"

        # Revoke the key
        r = client.post('/api/v1/keys/revoke',
                        headers={'X-API-Key': 'test-api-key-abc123'})
        assert r.status_code == 200, "Revocation endpoint failed"

        # Immediately attempt to use the revoked key — must fail
        r = client.get('/api/v1/posts',
                       headers={'X-API-Key': 'test-api-key-abc123'})
        assert r.status_code == 401, (
            "Revoked API key accepted immediately after revocation. "
            "Cache entry was not invalidated on revocation."
        )
