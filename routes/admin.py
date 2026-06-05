import logging
from flask import Blueprint, render_template, request, redirect, session
from database import db
from models.user import User, UserStats
from models.post import Post
from models.session import Session, AuditLog
from models.notification import Notification
from utils.auth import is_session_admin
from utils.cache import cache_clear
from utils.notifications import flush_pending, get_pending_count
from utils.stats import update_user_stats, refresh_post_metrics
import config

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def admin_required():
    return not is_session_admin()


@admin_bp.route('')
@admin_bp.route('/')
def dashboard():
    if not is_session_admin():
        return redirect('/')

    flush_pending()
    pending_count = get_pending_count()

    total_users = User.query.count()
    total_posts = Post.query.count()
    active_sessions = Session.query.filter_by(is_active=True).count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    posts = Post.query.all()
    for p in posts:
        refresh_post_metrics(p.id)

    users = User.query.all()
    for u in users:
        update_user_stats(u.id)

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_posts=total_posts,
                           active_sessions=active_sessions,
                           pending_count=pending_count,
                           recent_users=recent_users)


@admin_bp.route('/users')
def admin_users():
    if not is_session_admin():
        return redirect('/')

    users = User.query.all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/deactivate', methods=['POST'])
def deactivate_user(user_id):
    if not is_session_admin():
        return redirect('/')

    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()

    admin_user = User.query.filter_by(username=session.get('user')).first()
    log = AuditLog(
        admin_id=admin_user.id,
        action='deactivate',
        target_type='user',
        target_id=user_id
    )
    db.session.add(log)
    db.session.commit()

    cache_clear()
    logger.info(f"Admin deactivated user {user_id}")
    return redirect('/admin/users')


@admin_bp.route('/users/<int:user_id>/make_admin', methods=['POST'])
def make_admin(user_id):
    if not is_session_admin():
        return redirect('/')

    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()

    admin_user = User.query.filter_by(username=session.get('user')).first()
    log = AuditLog(
        admin_id=admin_user.id,
        action='make_admin',
        target_type='user',
        target_id=user_id
    )
    db.session.add(log)
    db.session.commit()

    cache_clear()
    logger.info(f"Admin granted admin to user {user_id}")
    return redirect('/admin/users')


@admin_bp.route('/features', methods=['GET'])
def feature_flags():
    if not is_session_admin():
        return redirect('/')
    return render_template('admin/features.html', features=config.FEATURES)


@admin_bp.route('/features', methods=['POST'])
def update_features():
    if not is_session_admin():
        return redirect('/')

    for flag_name in config.FEATURES:
        value = request.form.get(flag_name, 'false')
        config.FEATURES[flag_name] = value == 'true'

    logger.info("Feature flags updated")
    return redirect('/admin')
