import logging
from database import db
from models.notification import Notification

logger = logging.getLogger(__name__)

_pending_notifications = []


def create_notification(user_id, actor_id, type, reference_id):
    n = Notification(
        user_id=user_id,
        actor_id=actor_id,
        type=type,
        reference_id=reference_id
    )
    db.session.add(n)
    _pending_notifications.append({
        'user_id': user_id,
        'type': type
    })
    logger.info(f"Creating notification: type={type}, user={user_id}")


def get_pending_count():
    return len(_pending_notifications)


def flush_pending():
    _pending_notifications.clear()
