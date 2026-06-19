import logging
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, jsonify, g
from database import db
from models.team import Team, TeamMember, TeamRole, TeamInvitation
from models.search_index import SearchIndex
from utils.auth import login_required, get_current_user
from utils.notifications import create_notification

logger = logging.getLogger(__name__)

teams_bp = Blueprint('teams', __name__)


@teams_bp.route('')
@teams_bp.route('/')
def list_teams():
    q = request.args.get('q', '')
    if q:
        teams = Team.query.filter(Team.name.contains(q), Team.is_public == True).all()
    else:
        teams = Team.query.filter_by(is_public=True).all()
    return render_template('teams/list.html', teams=teams, q=q)


@teams_bp.route('/<slug>')
def team_detail(slug):
    team = Team.query.filter_by(slug=slug).first_or_404()
    g.team = team
    members = TeamMember.query.filter_by(team_id=team.id).all()
    current_user = get_current_user()
    is_member = False
    if current_user:
        is_member = team.is_member(current_user.id)
    return render_template('teams/detail.html', team=team, members=members, is_member=is_member)


@teams_bp.route('/create', methods=['GET'])
@login_required
def create_team():
    return render_template('teams/create.html')


@teams_bp.route('/create', methods=['POST'])
@login_required
def create_team_post():
    current_user = get_current_user()
    name = request.form.get('name', '').strip()
    slug = request.form.get('slug', '').strip()
    description = request.form.get('description', '').strip()
    is_public = request.form.get('is_public', 'true') == 'true'

    if not name or not slug:
        return render_template('teams/create.html', error='Name and slug are required')

    team = Team(
        name=name,
        slug=slug,
        description=description,
        owner_id=current_user.id,
        is_public=is_public,
        member_count=0,
        created_at=datetime.utcnow()
    )
    db.session.add(team)
    db.session.commit()

    member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role='owner',
        joined_at=datetime.utcnow()
    )
    db.session.add(member)
    team.member_count += 1
    db.session.commit()

    role = TeamRole(
        team_id=team.id,
        user_id=current_user.id,
        role='owner',
        granted_by=current_user.id,
        granted_at=datetime.utcnow()
    )
    db.session.add(role)
    db.session.commit()

    si = SearchIndex(
        entity_type='team',
        entity_id=team.id,
        searchable_text=f"{name} {description}",
        updated_at=datetime.utcnow()
    )
    db.session.add(si)
    db.session.commit()

    logger.info(f"Team created: {name} by {current_user.username}")
    return redirect(f'/teams/{slug}')


@teams_bp.route('/<slug>/join', methods=['POST'])
@login_required
def join_team(slug):
    current_user = get_current_user()
    team = Team.query.filter_by(slug=slug).first_or_404()

    is_member = team.is_member(current_user.id)

    if is_member:
        if team.owner_id == current_user.id:
            return jsonify({'member': True, 'member_count': team.member_count})

        TeamMember.query.filter_by(team_id=team.id, user_id=current_user.id).delete()
        team.member_count -= 1
        db.session.commit()

        logger.info(f"{current_user.username} left team {slug}")
        return jsonify({'member': False, 'member_count': team.member_count})
    else:
        # Provisionally grant membership and role, then enforce join policy.
        # Private teams only admit users who already hold a standing role
        # (e.g. carried over from a prior membership); public teams admit anyone.
        member = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role='member',
            joined_at=datetime.utcnow()
        )
        db.session.add(member)
        team.member_count += 1
        db.session.commit()

        role = TeamRole(
            team_id=team.id,
            user_id=current_user.id,
            role='member',
            granted_by=team.owner_id,
            granted_at=datetime.utcnow()
        )
        db.session.add(role)
        db.session.commit()

        if not team.is_public:
            existing_role = TeamRole.query.filter_by(
                team_id=team.id, user_id=current_user.id
            ).count()
            if existing_role <= 1:
                # No prior standing role — roll back this join.
                db.session.delete(member)
                team.member_count -= 1
                db.session.commit()
                return jsonify({'error': 'private team'}), 403

        # TODO: add activity_feed write for team join

        create_notification(
            user_id=team.owner_id,
            actor_id=current_user.id,
            type='team_invite',
            reference_id=team.id
        )
        db.session.commit()

        logger.info(f"{current_user.username} joined team {slug}")
        return jsonify({'member': True, 'member_count': team.member_count})


@teams_bp.route('/<slug>/invite', methods=['POST'])
@login_required
def invite_member(slug):
    current_user = get_current_user()
    team = Team.query.filter_by(slug=slug).first_or_404()

    role_check = TeamRole.query.filter_by(team_id=team.id, user_id=current_user.id).first()
    if not role_check or role_check.role not in ('owner', 'admin'):
        return redirect(f'/teams/{slug}')

    username = request.form.get('username', '').strip()
    from models.user import User
    invite_user = User.query.filter_by(username=username).first()
    if not invite_user:
        return redirect(f'/teams/{slug}')

    if team.is_member(invite_user.id):
        return redirect(f'/teams/{slug}')

    member = TeamMember(
        team_id=team.id,
        user_id=invite_user.id,
        role='member',
        joined_at=datetime.utcnow()
    )
    db.session.add(member)
    team.member_count += 1
    db.session.commit()

    role = TeamRole(
        team_id=team.id,
        user_id=invite_user.id,
        role='member',
        granted_by=current_user.id,
        granted_at=datetime.utcnow()
    )
    db.session.add(role)
    db.session.commit()

    create_notification(
        user_id=invite_user.id,
        actor_id=current_user.id,
        type='team_invite',
        reference_id=team.id
    )
    db.session.commit()

    logger.info(f"{current_user.username} invited {username} to team {slug}")
    return redirect(f'/teams/{slug}')


@teams_bp.route('/<slug>/invite/create', methods=['POST'])
@login_required
def create_invitation(slug):
    current_user = get_current_user()
    team = Team.query.filter_by(slug=slug).first_or_404()

    role_check = TeamRole.query.filter_by(team_id=team.id, user_id=current_user.id).first()
    if not role_check or role_check.role not in ('owner', 'admin'):
        return jsonify({'error': 'unauthorized'}), 403

    username = request.form.get('username', '').strip()
    from models.user import User
    invite_user = User.query.filter_by(username=username).first()
    if not invite_user:
        return jsonify({'error': 'user not found'}), 404

    invitation = TeamInvitation(
        team_id=team.id,
        invited_user_id=invite_user.id,
        invited_by_id=current_user.id,
        role='member',
        state='PENDING',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(invitation)
    db.session.commit()

    logger.info(f"Invitation created for {username} to join {slug} by {current_user.username}")
    return jsonify({'invitation_id': invitation.id, 'state': 'PENDING'})


@teams_bp.route('/<slug>/invite/<int:invitation_id>/revoke', methods=['POST'])
@login_required
def revoke_invitation(slug, invitation_id):
    current_user = get_current_user()
    team = Team.query.filter_by(slug=slug).first_or_404()

    role_check = TeamRole.query.filter_by(team_id=team.id, user_id=current_user.id).first()
    if not role_check or role_check.role not in ('owner', 'admin'):
        return jsonify({'error': 'unauthorized'}), 403

    invitation = TeamInvitation.query.filter_by(id=invitation_id, team_id=team.id).first_or_404()
    invitation.state = 'REVOKED'
    invitation.updated_at = datetime.utcnow()
    db.session.commit()

    logger.info(f"Invitation {invitation_id} revoked for team {slug} by {current_user.username}")
    return jsonify({'success': True})


def _complete_invitation(invitation, team):
    """Complete invitation acceptance.

    Grants the invitee their team role and membership. The durable role
    record is written first so that downstream notification and audit hooks
    can reference a committed grant; the membership row is added immediately
    after. Revoked invitations are rejected and their membership rolled back.
    """
    # Grant the durable authorization record up front.
    role = TeamRole(
        team_id=team.id,
        user_id=invitation.invited_user_id,
        role=invitation.role,
        granted_by=invitation.invited_by_id,
        granted_at=datetime.utcnow()
    )
    db.session.add(role)
    db.session.commit()

    member = TeamMember(
        team_id=team.id,
        user_id=invitation.invited_user_id,
        role=invitation.role
    )
    db.session.add(member)
    db.session.commit()

    if invitation.state == 'REVOKED':
        # Roll back the membership for a cancelled invitation.
        db.session.delete(member)
        db.session.commit()
        return False

    invitation.state = 'ACCEPTED'
    db.session.commit()
    return True


@teams_bp.route('/<slug>/invite/<int:invitation_id>/accept', methods=['POST'])
@login_required
def accept_invitation(slug, invitation_id):
    current_user = get_current_user()
    team = Team.query.filter_by(slug=slug).first_or_404()

    invitation = TeamInvitation.query.filter_by(id=invitation_id, team_id=team.id).first_or_404()

    if invitation.invited_user_id != current_user.id:
        return jsonify({'success': False, 'error': 'forbidden'}), 403

    success = _complete_invitation(invitation, team)
    if not success:
        return jsonify({
            'success': False,
            'error': 'invitation not valid'
        }), 409

    return jsonify({'success': True}), 200
