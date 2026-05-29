import uuid
from datetime import datetime
from app import create_app
from database import db
from models.user import User, UserProfile, UserStats
from models.post import Post, PostMetrics
from models.team import Team, TeamMember, TeamRole
from models.session import Session
from models.skill import Skill


def seed_data():
    admin = User(
        username='admin',
        email='admin@flock.local',
        display_name='Admin',
        is_admin=True,
        api_key=str(uuid.uuid4()).replace('-', ''),
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()

    admin_profile = UserProfile(
        user_id=admin.id,
        display_name='Admin',
        updated_at=datetime.utcnow()
    )
    db.session.add(admin_profile)
    db.session.commit()

    admin_stats = UserStats(user_id=admin.id, last_active=datetime.utcnow())
    db.session.add(admin_stats)
    db.session.commit()

    alice = User(
        username='alice',
        email='alice@example.com',
        display_name='Alice Chen',
        bio='Builder. Creator. Thinker.',
        location='San Francisco',
        website='https://alice.dev',
        follower_count=2,
        following_count=1,
        post_count=2,
        api_key=str(uuid.uuid4()).replace('-', ''),
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    alice.set_password('password')
    db.session.add(alice)
    db.session.commit()

    alice_profile = UserProfile(
        user_id=alice.id,
        display_name='Alice Chen',
        bio='Builder. Creator. Thinker.',
        location='San Francisco',
        website='https://alice.dev',
        github_url='https://github.com/alice',
        updated_at=datetime.utcnow()
    )
    db.session.add(alice_profile)
    db.session.commit()

    alice_stats = UserStats(
        user_id=alice.id,
        follower_count=2,
        following_count=1,
        post_count=2,
        last_active=datetime.utcnow()
    )
    db.session.add(alice_stats)
    db.session.commit()

    bob = User(
        username='bob',
        email='bob@example.com',
        display_name='Bob Martinez',
        bio='Open source enthusiast.',
        location='Austin, TX',
        follower_count=1,
        following_count=2,
        post_count=1,
        api_key=str(uuid.uuid4()).replace('-', ''),
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    bob.set_password('password')
    db.session.add(bob)
    db.session.commit()

    bob_profile = UserProfile(
        user_id=bob.id,
        display_name='Bob Martinez',
        bio='Open source enthusiast.',
        location='Austin, TX',
        updated_at=datetime.utcnow()
    )
    db.session.add(bob_profile)
    db.session.commit()

    bob_stats = UserStats(
        user_id=bob.id,
        follower_count=1,
        following_count=2,
        post_count=1,
        last_active=datetime.utcnow()
    )
    db.session.add(bob_stats)
    db.session.commit()

    post1 = Post(
        user_id=alice.id,
        content='Just launched my new project! Check it out at github.com/alice/project #python #opensource',
        like_count=3,
        comment_count=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(post1)
    db.session.commit()

    pm1 = PostMetrics(post_id=post1.id, like_count=3, comment_count=1, updated_at=datetime.utcnow())
    db.session.add(pm1)
    db.session.commit()

    post2 = Post(
        user_id=alice.id,
        content='Working on something exciting. Stay tuned! #buildinpublic',
        like_count=1,
        comment_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(post2)
    db.session.commit()

    pm2 = PostMetrics(post_id=post2.id, like_count=1, comment_count=0, updated_at=datetime.utcnow())
    db.session.add(pm2)
    db.session.commit()

    post3 = Post(
        user_id=bob.id,
        content='Great discussion at the meetup tonight. Lots of energy in the Python community #python',
        like_count=2,
        comment_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(post3)
    db.session.commit()

    pm3 = PostMetrics(post_id=post3.id, like_count=2, comment_count=0, updated_at=datetime.utcnow())
    db.session.add(pm3)
    db.session.commit()

    skill1 = Skill(user_id=alice.id, name='Python')
    skill2 = Skill(user_id=alice.id, name='Flask')
    skill3 = Skill(user_id=bob.id, name='JavaScript')
    db.session.add_all([skill1, skill2, skill3])
    db.session.commit()

    team = Team(
        name='Flock Core',
        slug='flock-core',
        description='The core team building Flock.',
        owner_id=alice.id,
        is_public=True,
        member_count=2,
        created_at=datetime.utcnow()
    )
    db.session.add(team)
    db.session.commit()

    tm1 = TeamMember(team_id=team.id, user_id=alice.id, role='owner', joined_at=datetime.utcnow())
    tm2 = TeamMember(team_id=team.id, user_id=bob.id, role='member', joined_at=datetime.utcnow())
    db.session.add_all([tm1, tm2])
    db.session.commit()

    tr1 = TeamRole(team_id=team.id, user_id=alice.id, role='owner', granted_by=alice.id, granted_at=datetime.utcnow())
    tr2 = TeamRole(team_id=team.id, user_id=bob.id, role='member', granted_by=alice.id, granted_at=datetime.utcnow())
    db.session.add_all([tr1, tr2])
    db.session.commit()

    print("Seed data created successfully.")
    print(f"  Users: admin, alice, bob")
    print(f"  Default admin password: admin123")
    print(f"  Default user password: password")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_data()
    print("Database initialized.")
