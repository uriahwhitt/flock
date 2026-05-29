import logging
from flask import Blueprint, render_template, request, redirect, jsonify
from database import db
from models.notification import Notification
from utils.auth import login_required, get_current_user

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('')
@notifications_bp.route('/')
@login_required
def list_notifications():
    current_user = get_current_user()
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.is_read.asc(), Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)


@notifications_bp.route('/unread_count')
@login_required
def unread_count():
    current_user = get_current_user()
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@notifications_bp.route('/mark_read', methods=['POST'])
@login_required
def mark_read():
    current_user = get_current_user()
    data = request.get_json()
    notification_id = data.get('notification_id')

    n = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    if n:
        n.is_read = True
        db.session.commit()
        return jsonify({'success': True})

    logger.warning(f"Notification {notification_id} not found for user {current_user.id}")
    return jsonify({'success': False})


@notifications_bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    current_user = get_current_user()
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    logger.info(f"Marked all notifications read for user {current_user.id}")
    return redirect('/notifications')
