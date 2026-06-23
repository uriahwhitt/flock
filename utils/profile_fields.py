ALLOWED_FIELDS = {'display_name', 'bio', 'location', 'website', 'github_url'}


def filter_profile_fields(data):
    """Return only the whitelisted profile fields from a dict."""
    return {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
