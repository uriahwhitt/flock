import re


def is_valid_username(username):
    if not username or len(username) < 3 or len(username) > 30:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))


def is_valid_email(email):
    if not email:
        return False
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))
