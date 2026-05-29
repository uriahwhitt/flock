from flask import Flask
from database import db, init_db
import config


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    init_db(app)

    from routes.auth import auth_bp
    from routes.feed import feed_bp
    from routes.profile import profile_bp
    from routes.teams import teams_bp
    from routes.projects import projects_bp
    from routes.notifications import notifications_bp
    from routes.messages import messages_bp
    from routes.search import search_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(feed_bp, url_prefix='/feed')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(teams_bp, url_prefix='/teams')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(messages_bp, url_prefix='/messages')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
