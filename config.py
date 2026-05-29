DEBUG = True
SECRET_KEY = 'flock-dev-secret-2023'
SQLALCHEMY_DATABASE_URI = 'sqlite:///flock.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
UPLOAD_FOLDER = 'static/uploads'
POSTS_PER_PAGE = 20
NOTIFICATIONS_POLL_INTERVAL = 30

FEATURES = {
    'hashtags': True,
    'endorsements': True,
    'projects': True,
    'messages': False,
    'job_board': False,
    'analytics': False,
}
