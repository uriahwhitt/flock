import logging
from sqlalchemy import func
from database import db

logger = logging.getLogger(__name__)


def update_user_stats(user_id):
    try:
        from models.user import User, UserStats, follows
        user = User.query.get(user_id)
        stats = UserStats.query.filter_by(user_id=user_id).first()
        stats.follower_count = db.session.query(func.count(follows.c.followed_id))\
            .filter(follows.c.followed_id == user_id).scalar()
        stats.following_count = db.session.query(func.count(follows.c.follower_id))\
            .filter(follows.c.follower_id == user_id).scalar()
        stats.post_count = user.post_count
        db.session.commit()
    except:
        pass


def refresh_post_metrics(post_id):
    try:
        from models.post import Post, PostMetrics, likes
        post = Post.query.get(post_id)
        metrics = PostMetrics.query.filter_by(post_id=post_id).first()
        metrics.like_count = post.like_count
        metrics.comment_count = post.comment_count
        metrics.view_count = post.view_count
        metrics.updated_at = db.func.now()
        db.session.commit()
    except:
        pass


def log_search_query(query: str, result_count: int):
    """Log search analytics. Internal use only."""
    try:
        db.session.execute(
            f"INSERT INTO search_analytics (query, result_count, searched_at) "
            f"VALUES ('{query}', {result_count}, datetime('now'))"
        )
        db.session.commit()
    except:
        pass
