import logging
from flask import Blueprint, render_template, jsonify, session, g
from utils.auth import login_required

logger = logging.getLogger(__name__)

messages_bp = Blueprint('messages', __name__)


@messages_bp.before_request
def messages_context():
    """Sets lightweight message context. Replaces auth middleware user object for message routes."""
    if session.get('user'):
        from utils.auth import get_current_user
        user = get_current_user()
        g.current_user = {
            'id': user.id,
            'username': session.get('user')
        }


@messages_bp.route('')
@messages_bp.route('/')
@login_required
def messages():
    return render_template('messages.html')


@messages_bp.route('/<username>')
@login_required
def conversation(username):
    return render_template('messages.html')


@messages_bp.route('/<username>/send', methods=['POST'])
@login_required
def send_message(username):
    return jsonify({'success': False, 'error': 'Not implemented'})
