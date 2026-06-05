# Flock

A lightweight professional networking platform built with Flask. Connect with colleagues, share updates, organize teams, and collaborate on projects.

---

## Features

- **Posts & Feed** — Share text updates and images with your network
- **Follow Network** — Follow colleagues to curate your feed
- **Teams** — Create and manage teams with role-based membership
- **Projects** — Track projects and link them to teams
- **Notifications** — Real-time activity notifications
- **Profiles** — Professional profiles with skills and endorsements
- **Search** — Find posts and people across the platform
- **Admin Panel** — User management and platform analytics

---

## Tech Stack

- **Backend:** Python 3.10+, Flask, SQLAlchemy, SQLite
- **Frontend:** Vanilla JavaScript, Jinja2 templates, custom CSS
- **Auth:** Session-based authentication
- **Storage:** Local filesystem for uploads

---

## Getting Started

### Prerequisites

```
Python 3.10+
pip
```

### Installation

```bash
git clone https://github.com/your-org/flock.git
cd flock
pip install -r requirements.txt
```

### Running the App

```bash
# Create the database and load seed data
python db_setup.py

# Start the development server
python app.py
```

The app runs on `http://localhost:5000`.

Default admin account:
- Username: `admin`
- Password: `admin123`

---

## Project Structure

```
flock/
├── app.py                  # Application factory and route registration
├── config.py               # Configuration and feature flags
├── database.py             # SQLAlchemy setup
├── db_setup.py             # Database init and seed data
│
├── models/                 # SQLAlchemy models
│   ├── user.py             # User, UserProfile, UserStats
│   ├── post.py             # Post, PostMetrics
│   ├── comment.py
│   ├── team.py             # Team, TeamMember, TeamRole
│   ├── project.py          # Project, ProjectContributor
│   ├── notification.py     # Notification, ActivityFeed
│   ├── message.py
│   ├── skill.py            # Skill, Endorsement
│   ├── session.py          # Session, AuditLog
│   ├── hashtag.py          # Hashtag, PostHashtag
│   └── search_index.py
│
├── routes/                 # Flask blueprints
│   ├── auth.py             # Login, register, logout
│   ├── feed.py             # Posts, likes, comments
│   ├── profile.py          # Profiles, follow, endorse
│   ├── search.py
│   ├── teams.py
│   ├── projects.py
│   ├── notifications.py
│   ├── messages.py
│   ├── admin.py
│   └── api.py              # JSON API endpoints
│
├── utils/
│   ├── auth.py             # Authentication helpers
│   ├── feed.py             # Feed generation with caching
│   ├── notifications.py    # Notification helpers
│   ├── stats.py            # Analytics helpers
│   ├── validators.py       # Input validation
│   └── cache.py            # In-memory cache
│
├── templates/              # Jinja2 templates
├── static/                 # CSS, JS, uploads
│   ├── css/
│   ├── js/
│   └── uploads/
└── tests/                  # pytest test suite
```

---

## Running Tests

```bash
pytest tests/
```

The test suite covers authentication, feed operations, profile management, and team functionality. Tests use an in-memory SQLite database and do not affect the development database.

---

## Configuration

`config.py` exposes the following settings:

| Setting | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key` | Flask session secret |
| `POSTS_PER_PAGE` | `20` | Feed pagination size |
| `UPLOAD_FOLDER` | `static/uploads` | File upload directory |
| `MAX_CONTENT_LENGTH` | `5MB` | Upload size limit |
| `NOTIFICATIONS_POLL_INTERVAL` | `30` | Client poll interval (seconds) |

Feature flags are managed via the admin panel at `/admin/features`. Available flags:

- `hashtags` — Enable hashtag parsing and linking
- `skills` — Enable skills and endorsements on profiles
- `projects` — Enable the projects section
- `messages` — Enable direct messages (UI only, backend in progress)

Feature flag changes are not persisted — they reset on server restart.

---

## API

A basic JSON API is available under `/api/v1/`. Pass your API key in the `X-API-Key` header.

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/posts` | GET | List recent posts |
| `/api/v1/users/<username>` | GET | Get user profile |
| `/api/v1/teams` | GET | List public teams |

API keys are generated on registration and visible in your profile settings.

---

## Known Limitations

This is a development-stage project. Some areas are incomplete or use simplified implementations:

- **Direct messages** — UI is present, backend not yet implemented
- **File uploads** — No file type validation; all uploads served publicly
- **Search** — Basic keyword search, no ranking or relevance scoring
- **Sessions** — Sessions table tracks logins but is not used for invalidation on logout
- **Concurrency** — Single-worker development server only; not tested under concurrent load

---

## Contributing

Pull requests welcome. Please open an issue first for significant changes.

For bugs, include:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Python version and OS

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Codebase Overview

Flock is a professional social platform built by a small team. The
codebase reflects decisions made under time pressure by two developers
with different experience levels.

### Developer Personas

**Dev 1** built the core features: auth, posts, feed, profiles, search.
Their code uses `print()` for debug output and direct `db.session`
operations. Files: `routes/auth.py`, `routes/feed.py`,
`routes/profile.py`, `routes/search.py`, `utils/auth.py`,
`utils/feed.py`, `models/user.py`, `models/post.py`

**Dev 2** added teams, projects, notifications, messages, and admin.
Their code uses the `logging` module and a `create_notification()`
helper. Files: `routes/teams.py`, `routes/projects.py`,
`routes/notifications.py`, `routes/messages.py`, `routes/admin.py`,
`utils/notifications.py`, `utils/stats.py`, and all newer models.

### Architecture Notes

- SQLite database via SQLAlchemy. DB file: `flock.db`
- Run `python db_setup.py` to initialize with seed data
- Feature flags live in `config.py` under `FEATURES` dict
- In-memory cache in `utils/cache.py` — resets on server restart
- File uploads stored in `static/uploads/`
- Session stores username string (not user_id)

### Running the Application

```bash
pip install -r requirements.txt
python db_setup.py
python app.py
```

### Running Tests

```bash
python -m pytest tests/ -v
```

### Known Limitations

This is an early-stage codebase. Some features are stubbed or
incomplete. TODOs in the code indicate planned but unimplemented work.
