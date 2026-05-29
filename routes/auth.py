import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, flash
from sqlalchemy.exc import IntegrityError
from database import db
from models.user import User, UserProfile, UserStats
from models.session import Session

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if session.get('user'):
        return redirect('/feed')
    return redirect('/login')


@auth_bp.route('/login', methods=['GET'])
def login():
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return render_template('auth/login.html', error='Invalid username or password')

    session['user'] = user.username
    user.last_seen = datetime.utcnow()
    db.session.commit()

    s = Session(
        user_id=user.id,
        session_token=str(uuid.uuid4()),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    db.session.add(s)
    db.session.commit()

    print(f"[DEBUG] User {username} logged in")
    return redirect('/feed')


@auth_bp.route('/register', methods=['GET'])
def register():
    return render_template('auth/register.html')


@auth_bp.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    display_name = request.form.get('display_name', '').strip()

    if not username or not email or not password or not display_name:
        return render_template('auth/register.html', error='All fields are required')

    if User.query.filter_by(username=username).first():
        return render_template('auth/register.html', error='Username already taken')

    if User.query.filter_by(email=email).first():
        return render_template('auth/register.html', error='Email already registered')

    user = User(
        username=username,
        email=email,
        display_name=display_name,
        api_key=str(uuid.uuid4()).replace('-', ''),
        created_at=datetime.utcnow()
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_template('auth/register.html', error='Username already taken')

    profile = UserProfile(
        user_id=user.id,
        display_name=display_name,
        updated_at=datetime.utcnow()
    )
    db.session.add(profile)
    db.session.commit()

    stats = UserStats(
        user_id=user.id,
        last_active=datetime.utcnow()
    )
    db.session.add(stats)
    db.session.commit()

    s = Session(
        user_id=user.id,
        session_token=str(uuid.uuid4()),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )
    db.session.add(s)
    db.session.commit()

    session['user'] = user.username
    print(f"[DEBUG] New user registered: {username}")
    return redirect('/feed')


@auth_bp.route('/logout')
def logout():
    # TODO: update sessions table to mark session inactive
    session.clear()
    return redirect('/login')
