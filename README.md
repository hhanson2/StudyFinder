# StudyFinder

A study group finder for college students: register, search for study groups
by course code, create your own group, join or leave groups, schedule study
sessions, post to a group discussion, and track it all from a dashboard.

This build implements the full Phase 1 feature set from Team Deliverable 3
(UML class/sequence/use-case diagrams) and matches the Figma UI mockups:
a dark sidebar with Dashboard / My Groups / Search Groups / Create Group /
Sessions / Profile / Settings, plus the dashboard's Upcoming Session,
Popular Groups, and Notifications cards.

## Quick start (easiest — no MySQL required)

The app now falls back to a local SQLite file automatically if you don't
configure MySQL/Postgres, so you can run it with zero extra setup.

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

Open http://127.0.0.1:8000 in your browser. That's it — a `studyfinder.db`
SQLite file is created automatically next to `main.py`.

### Optional: load demo data

To make the dashboard look populated right away (matching the mockups),
run the seed script once after the server has started at least one time
(so the tables exist):

```bash
python seed.py
```

This creates a demo account you can log in with:

- **Email:** darren@uncc.edu
- **Password:** password123

along with a few sample study groups, a scheduled session, and a couple of
notifications.

## Using MySQL instead

If you'd rather use MySQL (as in the original deliverable), create a `.env`
file in the project root:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=studyfinder_db
```

and create the database first:

```sql
CREATE DATABASE studyfinder_db;
```

As long as `DB_HOST`, `DB_USER`, and `DB_NAME` are all set, the app will use
MySQL instead of SQLite.

## What's implemented

- **Auth** — register / log in (bcrypt-hashed passwords), persisted client-side
  after login so refreshing the page keeps you signed in.
- **Dashboard** — welcome header, quick search, your next upcoming session,
  the most popular open group (with a one-click Join), your recent
  notifications, and a grid of the groups you belong to.
- **My Groups** — every group you created or joined, each opening a detail
  view with its members, sessions, and discussion posts.
- **Search Groups** — search by course code or group name, with live member
  counts and a Join button.
- **Create Group** — name, course code, description, max members, status.
- **Sessions** — every upcoming session across all of your groups; you can
  also schedule a new session from within any group's detail view.
- **Profile** — your name, major, and stats (groups created, groups joined,
  upcoming sessions, discussion posts).
- **Settings** — edit your display name / major / school year, and log out.
- **Notifications** — automatically generated when someone joins your group,
  a session is scheduled, or someone posts to a group discussion.

## API docs

While the server is running, interactive API docs are available at
http://127.0.0.1:8000/docs.

## Project structure

```
main.py                  FastAPI app + router wiring + static frontend mount
database.py               SQLAlchemy engine/session setup (SQLite/MySQL/Postgres)
models.py                 SQLAlchemy ORM models
schemas.py                Pydantic request/response schemas
security.py               Password hashing helpers
seed.py                   Optional demo-data seeder
routers/
  auth.py                 /auth/register, /auth/login
  users.py                 /users/... (profile, groups, sessions, update)
  study_groups.py          /study-groups/... (CRUD, search)
  group_members.py         /study-groups/{id}/members/... (join/leave)
  study_sessions.py        session scheduling
  discussion_posts.py      group discussion posts
  dashboard.py              /dashboard/{user_id} aggregate view
frontend/
  index.html               App shell (auth view + sidebar app view)
  styles.css                Styling matching the Figma mockups
  app.js                    All client-side logic (fetches the API above)
```
