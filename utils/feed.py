import config
from database import db
from utils.cache import cache_get, cache_set

PAGE_SIZE = config.POSTS_PER_PAGE


def get_feed(user_id, page=1):
    print(f"[DEBUG] Generating feed for user {user_id}, page {page}")

    cache_key = f"feed:{user_id}:{page}"
    cached = cache_get(cache_key)
    if cached:
        print(f"[DEBUG] Cache hit for {cache_key}")
        return cached

    print(f"[DEBUG] Cache miss — querying DB")

    from models.post import Post
    # TODO: filter feed to only show posts from followed users and self
    pagination = Post.query.filter_by(is_deleted=False)\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=PAGE_SIZE, error_out=False)

    cache_set(cache_key, pagination, ttl=300)
    return pagination
