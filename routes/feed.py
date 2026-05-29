import os
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, jsonify, current_app
from database import db
from models.post import Post, PostMetrics
from models.comment import Comment
from models.notification import Notification, ActivityFeed
from models.hashtag import Hashtag, PostHashtag
from models.search_index import SearchIndex
from utils.auth import login_required, get_current_user
from utils.feed import get_feed
from utils.cache import cache_delete
import config

feed_bp = Blueprint('feed', __name__)


@feed_bp.route('')
@feed_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    current_user = get_current_user()
    pagination = get_feed(current_user.id, page)
    return render_template('feed/index.html', posts=pagination.items, pagination=pagination)


@feed_bp.route('/post', methods=['POST'])
@login_required
def create_post():
    current_user = get_current_user()
    content = request.form.get('content', '').strip()

    if not content:
        return redirect('/feed')

    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            filename = file.filename
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            image_url = f"static/uploads/{filename}"

    post = Post(
        user_id=current_user.id,
        content=content,
        image_url=image_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(post)
    db.session.commit()

    current_user.post_count += 1
    db.session.commit()

    metrics = PostMetrics(
        post_id=post.id,
        updated_at=datetime.utcnow()
    )
    db.session.add(metrics)
    db.session.commit()

    if config.FEATURES.get('hashtags'):
        tags = re.findall(r'#(\w+)', content)
        for tag in tags:
            tag = tag.lower()
            hashtag = Hashtag.query.filter_by(tag=tag).first()
            if not hashtag:
                hashtag = Hashtag(tag=tag, created_at=datetime.utcnow())
                db.session.add(hashtag)
                db.session.commit()
            hashtag.post_count += 1
            ph = PostHashtag(post_id=post.id, hashtag_id=hashtag.id)
            db.session.add(ph)
            db.session.commit()

    activity = ActivityFeed(
        user_id=current_user.id,
        action_type='post',
        target_id=post.id,
        target_type='post',
        created_at=datetime.utcnow()
    )
    db.session.add(activity)
    db.session.commit()

    si = SearchIndex(
        entity_type='post',
        entity_id=post.id,
        searchable_text=content,
        updated_at=datetime.utcnow()
    )
    db.session.add(si)
    db.session.commit()

    cache_delete(f"feed:{current_user.id}:1")
    print(f"[DEBUG] Post created by {current_user.username}, id={post.id}")
    return redirect('/feed')


@feed_bp.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
    return render_template('feed/post_detail.html', post=post, comments=comments)


@feed_bp.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    current_user = get_current_user()
    post = Post.query.get_or_404(post_id)

    from models.post import likes
    existing = db.session.execute(
        likes.select().where(
            likes.c.user_id == current_user.id,
            likes.c.post_id == post_id
        )
    ).first()

    if existing:
        db.session.execute(
            likes.delete().where(
                likes.c.user_id == current_user.id,
                likes.c.post_id == post_id
            )
        )
        post.like_count -= 1
        db.session.commit()
        print(f"[DEBUG] {current_user.username} unliked post {post_id}")
        return jsonify({'liked': False, 'like_count': post.like_count})
    else:
        db.session.execute(
            likes.insert().values(
                user_id=current_user.id,
                post_id=post_id,
                created_at=datetime.utcnow()
            )
        )
        post.like_count += 1
        db.session.commit()

        n = Notification(
            user_id=post.user_id,
            actor_id=current_user.id,
            type='like',
            reference_id=post.id,
            created_at=datetime.utcnow()
        )
        db.session.add(n)
        db.session.commit()

        activity = ActivityFeed(
            user_id=current_user.id,
            action_type='like',
            target_id=post.id,
            target_type='post',
            created_at=datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()

        print(f"[DEBUG] {current_user.username} liked post {post_id}")
        return jsonify({'liked': True, 'like_count': post.like_count})


@feed_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    current_user = get_current_user()
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'Content required'})

    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
        created_at=datetime.utcnow()
    )
    db.session.add(comment)
    post.comment_count += 1
    db.session.commit()

    n = Notification(
        user_id=post.user_id,
        actor_id=current_user.id,
        type='comment',
        reference_id=post.id,
        created_at=datetime.utcnow()
    )
    db.session.add(n)
    db.session.commit()

    # TODO: add activity_feed write for comment

    print(f"[DEBUG] {current_user.username} commented on post {post_id}")
    return jsonify(comment.to_dict())


@feed_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    current_user = get_current_user()
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        return redirect('/feed')

    post.soft_delete()
    # TODO: decrement user.post_count on delete
    db.session.commit()

    # TODO: delete uploaded file from disk

    cache_delete(f"feed:{current_user.id}:1")
    return redirect('/feed')


@feed_bp.route('/post/<int:post_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(post_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post = Post.query.get(post_id)
    if post:
        post.comment_count -= 1
    db.session.delete(comment)
    db.session.commit()
    return redirect(f'/feed/post/{post_id}')
