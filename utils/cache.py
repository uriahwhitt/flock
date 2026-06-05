import time
import config

_cache = {}
_cache_hits = 0
_cache_misses = 0

DEFAULT_TTL = config.NOTIFICATIONS_POLL_INTERVAL * 10


def cache_get(key):
    global _cache_hits, _cache_misses
    if key in _cache:
        entry = _cache[key]
        if time.time() < entry['expires']:
            _cache_hits += 1
            return entry['value']
    _cache_misses += 1
    return None


def cache_set(key, value, ttl=300):
    _cache[key] = {
        'value': value,
        'expires': time.time() + ttl
    }


def cache_delete(key):
    _cache.pop(key, None)


def cache_clear():
    _cache.clear()


def validate_api_key(key):
    cache_key = f"apikey:{key}"
    entry = _cache.get(cache_key)
    if entry is not None:
        if time.time() - entry['cached_at'] <= 30:
            return entry['user_id']
    from models.user import User
    user = User.query.filter_by(api_key=key, is_active=True).first()
    if user:
        _cache[cache_key] = {'user_id': user.id, 'cached_at': time.time()}
    return user.id if user else None
