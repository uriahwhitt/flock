import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, jsonify, g, current_app
from database import db
from models.user import User, UserProfile
from models.notification import Notification, ActivityFeed
from models.skill import Skill, Endorsement
from models.search_index import SearchIndex
from models.user import follows
from utils.auth import login_required, get_current_user
from utils.cache import cache_get, cache_set, cache_delete
from utils.profile_fields import filter_profile_fields

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/<username>')
def view_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    activity = user.activity[-10:] if user.activity else []

    g.profile_user = user

    cache_key = f"profile:{username}"
    cached = cache_get(cache_key)
    if not cached:
        print(f"[DEBUG] Cache miss for profile {username}")
        cache_set(cache_key, user.to_dict(), ttl=300)

    current_user = get_current_user()
    is_following = False
    if current_user:
        is_following = current_user.is_following(user.id)

    return render_template('profile/view.html',
                           user=user,
                           profile=profile,
                           activity=activity,
                           is_following=is_following)


@profile_bp.route('/edit', methods=['GET'])
@login_required
def edit_profile():
    current_user = get_current_user()
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    return render_template('profile/edit.html', user=current_user, profile=profile)


@profile_bp.route('/edit', methods=['POST'])
@login_required
def edit_profile_post():
    current_user = get_current_user()
    display_name = request.form.get('display_name', '').strip()
    bio = request.form.get('bio', '').strip()
    location = request.form.get('location', '').strip()
    website = request.form.get('website', '').strip()

    avatar_url = current_user.avatar_url
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename:
            filename = file.filename
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            avatar_url = f"static/uploads/{filename}"
            # TODO: delete old avatar file from disk

    current_user.display_name = display_name
    current_user.bio = bio
    current_user.location = location
    current_user.website = website
    current_user.avatar_url = avatar_url
    db.session.commit()

    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if profile:
        profile.display_name = display_name
        profile.bio = bio
        profile.location = location
        profile.website = website
        profile.avatar_url = avatar_url
        profile.updated_at = datetime.utcnow()
        db.session.commit()

    si = SearchIndex.query.filter_by(entity_type='user', entity_id=current_user.id).first()
    if si:
        si.searchable_text = f"{current_user.username} {display_name}"
        si.updated_at = datetime.utcnow()
        db.session.commit()

    cache_delete(f"profile:{current_user.username}")
    print(f"[DEBUG] Profile updated for {current_user.username}")
    return redirect(f'/profile/{current_user.username}')


@profile_bp.route('/settings/update', methods=['POST'])
@login_required
def update_profile_settings():
    current_user = get_current_user()
    fields = filter_profile_fields(request.form.to_dict())
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if profile:
        for k, v in fields.items():
            if hasattr(profile, k):
                setattr(profile, k, v)
        profile.updated_at = datetime.utcnow()
        db.session.commit()
    print(f"[DEBUG] Profile settings updated for {current_user.username}")
    return redirect(f'/profile/{current_user.username}')


@profile_bp.route('/<username>/follow', methods=['POST'])
@login_required
def toggle_follow(username):
    current_user = get_current_user()
    target_user = User.query.filter_by(username=username).first_or_404()

    if current_user.id == target_user.id:
        return jsonify({'following': False, 'follower_count': target_user.follower_count})

    already_following = current_user.is_following(target_user.id)

    if already_following:
        db.session.execute(
            follows.delete().where(
                follows.c.follower_id == current_user.id,
                follows.c.followed_id == target_user.id
            )
        )
        db.session.commit()

        # TODO: decrement follower_count on unfollow
        current_user.following_count -= 1
        db.session.commit()

        print(f"[DEBUG] {current_user.username} unfollowed {username}")
        return jsonify({'following': False, 'follower_count': target_user.follower_count})
    else:
        db.session.execute(
            follows.insert().values(
                follower_id=current_user.id,
                followed_id=target_user.id,
                created_at=datetime.utcnow()
            )
        )
        db.session.commit()

        target_user.follower_count += 1
        db.session.commit()

        current_user.following_count += 1
        db.session.commit()

        n = Notification(
            user_id=target_user.id,
            actor_id=current_user.id,
            type='follow',
            reference_id=current_user.id,
            created_at=datetime.utcnow()
        )
        db.session.add(n)
        db.session.commit()

        activity = ActivityFeed(
            user_id=current_user.id,
            action_type='follow',
            target_id=target_user.id,
            target_type='user',
            created_at=datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()

        # TODO: update user_stats from follow route

        print(f"[DEBUG] {current_user.username} followed {username}")
        return jsonify({'following': True, 'follower_count': target_user.follower_count})


@profile_bp.route('/<username>/endorse/<int:skill_id>', methods=['POST'])
@login_required
def endorse_skill(username, skill_id):
    current_user = get_current_user()
    target_user = User.query.filter_by(username=username).first_or_404()
    skill = Skill.query.get_or_404(skill_id)

    if skill.user_id != target_user.id:
        return redirect(f'/profile/{username}')

    if current_user.id == target_user.id:
        flash('You cannot endorse your own skills', 'error')
        return redirect(f'/profile/{username}')

    existing = Endorsement.query.filter_by(
        skill_id=skill_id, endorser_id=current_user.id
    ).first()
    if existing:
        return redirect(f'/profile/{username}')

    endorsement = Endorsement(
        skill_id=skill_id,
        endorser_id=current_user.id,
        endorsed_id=target_user.id,
        created_at=datetime.utcnow()
    )
    db.session.add(endorsement)
    db.session.commit()

    print(f"[DEBUG] {current_user.username} endorsed skill {skill_id} for {username}")
    return redirect(f'/profile/{username}')
