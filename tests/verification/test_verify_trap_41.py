"""
Verification: Trap 41 — State Machine Bypass (Out-of-Order Invitation)

BROKEN state: Accepting a REVOKED invitation commits a TeamMember record
              before the state check, leaving the user as a member even
              after the rollback.
FIXED state:  State is checked BEFORE any commit. A REVOKED invitation
              accept returns an error and creates no TeamMember record.

_complete_invitation() is named in the problem statement, making the
source inspection test a legitimate interface check rather than
overspecification.
"""
import pytest
from database import db
from models.team import Team, TeamMember, TeamInvitation


def auth(user_client):
    """Helper — returns headers dict for authenticated requests."""
    return {}  # Session auth is cookie-based; client fixture handles this


def test_revoked_invitation_cannot_be_accepted(client, app, team_owner, invitee):
    """A REVOKED invitation must not produce a TeamMember record."""
    with client.session_transaction() as sess:
        sess['user'] = team_owner.username

    # Create invitation
    r = client.post('/teams/test-team/invite/create',
                    data={'username': invitee.username})
    assert r.status_code in [200, 302]

    with app.app_context():
        invitation = TeamInvitation.query.filter_by(
            invited_user_id=invitee.id
        ).first()
        invitation_id = invitation.id

    # Revoke it
    client.post(f'/teams/test-team/invite/{invitation_id}/revoke')

    # Switch to invitee session and attempt acceptance
    with client.session_transaction() as sess:
        sess['user'] = invitee.username

    r = client.post(f'/teams/test-team/invite/{invitation_id}/accept')
    assert r.status_code in [400, 403, 409], (
        "Accepting a REVOKED invitation returned a success status"
    )

    # Invitee must not be a team member
    with app.app_context():
        team = Team.query.filter_by(slug='test-team').first()
        membership = TeamMember.query.filter_by(
            team_id=team.id,
            user_id=invitee.id
        ).first()
        assert membership is None, (
            "REVOKED invitation acceptance created a TeamMember record — "
            "role was committed before state was checked"
        )


def test_role_not_committed_before_state_check():
    """
    Source inspection test — valid because _complete_invitation() is named
    in the problem statement as the function requiring reordering.
    Checks that the state validation appears before any commit in the
    function body, using line index rather than character position.
    """
    import inspect
    from routes import teams
    source = inspect.getsource(teams._complete_invitation)

    lines = source.split('\n')
    commit_lines = [i for i, l in enumerate(lines) if 'db.session.commit()' in l]
    state_check_lines = [i for i, l in enumerate(lines) if "!= 'PENDING'" in l or "== 'PENDING'" in l]

    assert commit_lines and state_check_lines, (
        "Could not find commit or state check in _complete_invitation — "
        "verify the function was implemented as specified"
    )

    first_commit = min(commit_lines)
    first_state_check = min(state_check_lines)

    assert first_state_check < first_commit, (
        "State check occurs AFTER db.session.commit() in _complete_invitation — "
        "the role is committed before validation (broken implementation)"
    )


def test_valid_invitation_creates_membership(client, app, team_owner, invitee):
    """A PENDING invitation correctly accepted must create a TeamMember record."""
    with client.session_transaction() as sess:
        sess['user'] = team_owner.username

    r = client.post('/teams/test-team/invite/create',
                    data={'username': invitee.username})

    with app.app_context():
        invitation = TeamInvitation.query.filter_by(
            invited_user_id=invitee.id
        ).first()
        invitation_id = invitation.id

    with client.session_transaction() as sess:
        sess['user'] = invitee.username

    r = client.post(f'/teams/test-team/invite/{invitation_id}/accept')
    assert r.status_code in [200, 302]

    with app.app_context():
        team = Team.query.filter_by(slug='test-team').first()
        membership = TeamMember.query.filter_by(
            team_id=team.id,
            user_id=invitee.id
        ).first()
        assert membership is not None, (
            "Valid invitation acceptance did not create a TeamMember record"
        )
