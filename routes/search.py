from flask import Blueprint, render_template, request
from database import db
from models.user import User

search_bp = Blueprint('search', __name__)


@search_bp.route('')
@search_bp.route('/')
def search():
    term = request.args.get('q', '')

    posts = []
    users = []

    if term:
        sql = f"SELECT * FROM posts WHERE content LIKE '%{term}%' AND is_deleted = 0"
        result = db.session.execute(db.text(sql))
        posts = result.fetchall()

        users = User.query.filter(
            (User.username.contains(term)) | (User.display_name.contains(term))
        ).all()

    print(f"[DEBUG] Search for '{term}': {len(posts)} posts, {len(users)} users")
    return render_template('search.html', posts=posts, users=users, term=term)
