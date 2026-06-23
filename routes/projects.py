import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, jsonify, g
from database import db
from models.project import Project, ProjectContributor
from models.team import TeamMember
from models.search_index import SearchIndex
from models.message import Message
from utils.auth import login_required, get_current_user
from utils.pagination import paginate
import config

logger = logging.getLogger(__name__)

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('')
@projects_bp.route('/')
def list_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()

    if config.FEATURES.get('projects') and config.FEATURES.get('messages'):
        for p in projects:
            p.unread_messages = _get_project_thread_count(p, g.current_user)

    return render_template('projects/list.html', projects=projects)


def _get_project_thread_count(project, user):
    """Get unread message count for project thread."""
    try:
        return Message.query.filter_by(
            project_id=project.id,
            recipient_id=user['id'],
            is_read=False
        ).count()
    except:
        return 0


@projects_bp.route('/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    contributors = ProjectContributor.query.filter_by(project_id=project_id).all()
    return render_template('projects/detail.html', project=project, contributors=contributors)


@projects_bp.route('/create', methods=['GET'])
@login_required
def create_project():
    from models.team import Team
    current_user = get_current_user()
    teams = Team.query.join(TeamMember, TeamMember.team_id == Team.id)\
        .filter(TeamMember.user_id == current_user.id).all()
    return render_template('projects/create.html', teams=teams)


@projects_bp.route('/create', methods=['POST'])
@login_required
def create_project_post():
    current_user = get_current_user()
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    status = request.form.get('status', 'active')
    repo_url = request.form.get('repo_url', '').strip()
    live_url = request.form.get('live_url', '').strip()
    team_id = request.form.get('team_id', None)

    if team_id:
        try:
            team_id = int(team_id)
        except (ValueError, TypeError):
            team_id = None

    project = Project(
        team_id=team_id,
        owner_id=current_user.id,
        title=title,
        description=description,
        status=status,
        repo_url=repo_url,
        live_url=live_url,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(project)
    db.session.commit()

    if team_id:
        team_members = TeamMember.query.filter_by(team_id=team_id).all()
        for tm in team_members:
            contributor = ProjectContributor(
                project_id=project.id,
                user_id=tm.user_id,
                role='contributor',
                added_at=datetime.utcnow()
            )
            db.session.add(contributor)
        db.session.commit()
        # TODO: sync project_contributors when new team members join after project creation

    si = SearchIndex(
        entity_type='project',
        entity_id=project.id,
        searchable_text=f"{title} {description}",
        updated_at=datetime.utcnow()
    )
    db.session.add(si)
    db.session.commit()

    logger.info(f"Project created: {title} by {current_user.username}")
    return redirect(f'/projects/{project.id}')

@projects_bp.route('/browse')
def browse_projects():
    page = int(request.args.get('page', 1))
    query = Project.query.order_by(Project.created_at.desc())
    result = paginate(query, page)
    return jsonify({
        'projects': [{'id': p.id, 'title': p.title} for p in result['items']],
        'total': result['total'],
        'page': result['page'],
        'pages': result['pages'],
    })

# TODO: implement project edit route
# TODO: implement project delete route
