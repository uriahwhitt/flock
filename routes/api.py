import logging
from flask import Blueprint, jsonify, request
from database import db
from models.user import User
from models.post import Post
from utils.cache import validate_api_key
import config

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/users/<username>')
def api_user(username):
    api_key = request.headers.get('X-API-Key')
    user = User.query.filter_by(username=username).first_or_404()
    return jsonify(user.to_dict())


@api_bp.route('/posts/<int:post_id>')
def api_post(post_id):
    api_key = request.headers.get('X-API-Key')
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict())


@api_bp.route('/posts')
def api_posts():
    api_key = request.headers.get('X-API-Key')
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(is_deleted=False)\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=config.POSTS_PER_PAGE, error_out=False)
    return jsonify([p.to_dict() for p in pagination.items])


@api_bp.route('/keys/revoke', methods=['POST'])
def revoke_api_key():
    key = request.headers.get('X-API-Key')
    if not key:
        return jsonify({'error': 'not found'}), 404
    user_id = validate_api_key(key)
    if not user_id:
        return jsonify({'error': 'not found'}), 404
    user = User.query.filter_by(api_key=key).first()
    if not user:
        return jsonify({'error': 'not found'}), 404
    user.api_key = None
    db.session.commit()
    return jsonify({'success': True})
