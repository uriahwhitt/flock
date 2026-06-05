"""
Verification: Trap 40 — Polyglot SQL Injection via Silent Truncation

BROKEN state: 33-char payload bypasses SearchIndex._sanitize_query()
              truncation boundary and injects into the search_analytics
              table via log_search_query() in utils/stats.py.
FIXED state:  log_search_query() uses parameterized queries. Raw search
              input cannot be used to inject SQL via the analytics logger.

FAIL-to-PASS tests:
  test_injection_payload_does_not_create_user
  test_analytics_table_not_exploitable

PASS-to-PASS tests (must not regress):
  test_truncation_boundary_safe
"""
import pytest

PADDING = 'a' * 32
INJECTION = (
    f"{PADDING}', 0); INSERT INTO users "
    f"(username, email, password_hash) "
    f"VALUES ('injected_trap40', 'x@x.com', 'x'); --"
)


def test_injection_payload_does_not_create_user(client, app):
    """SQL injection through search must not create unauthorized users."""
    client.get(f'/search?q={INJECTION}')

    with app.app_context():
        from models.user import User
        injected = User.query.filter_by(username='injected_trap40').first()
        assert injected is None, (
            "SQL injection via search analytics created an unauthorized user. "
            "log_search_query() in utils/stats.py uses string interpolation."
        )


def test_analytics_table_not_exploitable(client):
    """
    Source inspection test — valid because log_search_query() is named
    in the problem statement as the function requiring parameterization.
    Checks that the fix uses parameterized queries rather than f-string
    interpolation in the specific named function.
    """
    import inspect
    from utils import stats
    source = inspect.getsource(stats.log_search_query)

    has_fstring_sql = 'f"INSERT' in source or "f'INSERT" in source
    has_format_sql = '.format(' in source and 'INSERT' in source

    assert not has_fstring_sql and not has_format_sql, (
        "log_search_query() uses string interpolation in SQL — "
        "use parameterized queries instead"
    )


def test_truncation_boundary_safe(client, app):
    """32-char boundary must not produce SQL injection artifacts."""
    client.get('/search?q=' + 'a' * 31)
    client.get('/search?q=' + 'a' * 32)
    client.get('/search?q=' + 'a' * 33)

    with app.app_context():
        from models.search_index import SearchAnalytics
        rows = SearchAnalytics.query.filter(
            SearchAnalytics.query.contains('DROP') |
            SearchAnalytics.query.contains('INSERT INTO users') |
            SearchAnalytics.query.contains('--')
        ).count()
        assert rows == 0, (
            "SQL injection artifacts found in search_analytics table at the "
            "32-character truncation boundary."
        )
