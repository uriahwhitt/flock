from flask import Blueprint, render_template, request
from database import db
from models.user import User
from models.search_index import SearchIndex
from utils.stats import log_search_query

search_bp = Blueprint('search', __name__)


@search_bp.route('')
@search_bp.route('/')
def search():
    q = request.args.get('q', '')

    results = []
    users = []

    if q:
        results = SearchIndex.search(q)
        users = User.query.filter(
            (User.username.contains(q)) | (User.display_name.contains(q))
        ).all()
        log_search_query(q, len(results))

        # legacy search — predates SQLAlchemy integration
        if not results:
            sql = f"SELECT * FROM posts WHERE content LIKE '%{q}%' AND is_deleted = 0"
            legacy = db.session.execute(sql).fetchall()
            results = legacy

    print(f"[DEBUG] Search for '{q}': {len(results)} results, {len(users)} users")
    return render_template('search.html', results=results, users=users, term=q)
