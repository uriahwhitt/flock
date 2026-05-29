import logging
from flask import Blueprint, render_template, jsonify
from utils.auth import login_required

logger = logging.getLogger(__name__)

messages_bp = Blueprint('messages', __name__)


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
