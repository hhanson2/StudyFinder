"""
Seeds the StudyFinder database with demo data that mirrors the Figma
mockups (Alex Morgan's dashboard, groups, sessions, discussions, and
notifications), so the app looks populated the first time you run it.

Run once, after the server has created the tables:

    python seed.py

It is safe to run multiple times -- it checks for the demo user's email
before inserting anything.
"""

from datetime import datetime, timedelta

from database import Base, SessionLocal, engine
from models import (
    DiscussionPost,
    Notification,
    StudyGroup,
    StudyGroupMember,
    StudySession,
    User,
)
from security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    existing = db.query(User).filter(User.email == "alex.morgan@uncc.edu").first()

    if existing:
        print("Demo data already exists -- nothing to do.")
    else:
        alex = User(
            display_name="Alex Morgan",
            email="alex.morgan@uncc.edu",
            password_hash=hash_password("password123"),
            major="Computer Science",
            school_year="Senior",
        )
        maya = User(
            display_name="Maya Patel",
            email="maya.patel@uncc.edu",
            password_hash=hash_password("password123"),
            major="Computer Science",
            school_year="Junior",
        )
        jordan = User(
            display_name="Jordan Lee",
            email="jordan.lee@uncc.edu",
            password_hash=hash_password("password123"),
            major="Computer Science",
            school_year="Sophomore",
        )
        taylor = User(
            display_name="Taylor Kim",
            email="taylor.kim@uncc.edu",
            password_hash=hash_password("password123"),
            major="Information Technology",
            school_year="Junior",
        )

        db.add_all([alex, maya, jordan, taylor])
        db.commit()
        for u in (alex, maya, jordan, taylor):
            db.refresh(u)

        data_structures_squad = StudyGroup(
            group_name="Data Structures Squad",
            course_code="ITSC-2214",
            description="Practice trees, graphs, and weekly coding challenges.",
            creator_user_id=maya.id,
            status="open",
            max_members=10,
        )
        calculus_crew = StudyGroup(
            group_name="Calculus Crew",
            course_code="MATH-1242",
            description="Exam reviews and guided problem-solving sessions.",
            creator_user_id=alex.id,
            status="open",
            max_members=12,
        )
        code_collective = StudyGroup(
            group_name="Code Collective",
            course_code="ITSC-1213",
            description="Build projects and prepare for programming exams.",
            creator_user_id=alex.id,
            status="full",
            max_members=10,
        )
        chem_connect = StudyGroup(
            group_name="Chem Connect",
            course_code="CHEM-1251",
            description="Lab prep and problem sets for general chemistry.",
            creator_user_id=jordan.id,
            status="open",
            max_members=8,
        )
        database_study_hub = StudyGroup(
            group_name="Database Study Hub",
            course_code="ITSC-3155",
            description="SQL, normalization, and transaction design practice.",
            creator_user_id=alex.id,
            status="open",
            max_members=10,
        )

        db.add_all([
            data_structures_squad,
            calculus_crew,
            code_collective,
            chem_connect,
            database_study_hub,
        ])
        db.commit()

        for g in (
            data_structures_squad,
            calculus_crew,
            code_collective,
            chem_connect,
            database_study_hub,
        ):
            db.refresh(g)

        memberships = [
            # Alex is creator of Calculus Crew, Code Collective, Database Study
            # Hub (creators don't need a membership row), and joins these others:
            StudyGroupMember(group_id=data_structures_squad.id, user_id=alex.id),
            StudyGroupMember(group_id=chem_connect.id, user_id=alex.id),
            # Fill out membership counts to roughly match the mockups
            StudyGroupMember(group_id=data_structures_squad.id, user_id=jordan.id),
            StudyGroupMember(group_id=data_structures_squad.id, user_id=taylor.id),
            StudyGroupMember(group_id=calculus_crew.id, user_id=maya.id),
            StudyGroupMember(group_id=calculus_crew.id, user_id=jordan.id),
            StudyGroupMember(group_id=code_collective.id, user_id=maya.id),
            StudyGroupMember(group_id=code_collective.id, user_id=jordan.id),
            StudyGroupMember(group_id=code_collective.id, user_id=taylor.id),
            StudyGroupMember(group_id=chem_connect.id, user_id=maya.id),
        ]
        db.add_all(memberships)

        today_6pm = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
        if today_6pm < datetime.now():
            today_6pm += timedelta(minutes=5)

        sessions = [
            StudySession(
                group_id=calculus_crew.id,
                title="Calculus II Exam Review",
                location="Atkins Library • Room 218",
                scheduled_at=today_6pm,
                duration_minutes=90,
            ),
            StudySession(
                group_id=code_collective.id,
                title="Python Project Sprint",
                location=None,
                meeting_link="https://meet.google.com/studyfinder-demo",
                scheduled_at=datetime.now() + timedelta(days=1, hours=2),
                duration_minutes=60,
            ),
            StudySession(
                group_id=data_structures_squad.id,
                title="Graph Traversal Review",
                location="Woodward 106",
                scheduled_at=datetime.now() + timedelta(days=4),
                duration_minutes=75,
            ),
            StudySession(
                group_id=chem_connect.id,
                title="Chemistry Practice Problems",
                location="Science Building 104",
                scheduled_at=datetime.now() + timedelta(days=4, hours=1),
                duration_minutes=60,
            ),
            StudySession(
                group_id=calculus_crew.id,
                title="Midterm Practice",
                location="Atkins Library",
                scheduled_at=datetime.now() - timedelta(days=6),
                duration_minutes=75,
            ),
            StudySession(
                group_id=data_structures_squad.id,
                title="Linked Lists Lab",
                location="Woodward 106",
                scheduled_at=datetime.now() - timedelta(days=10),
                duration_minutes=60,
            ),
        ]
        db.add_all(sessions)

        # Discussion thread matching the mockup: Data Structures Squad
        db.commit()

        dijkstra_post = DiscussionPost(
            group_id=data_structures_squad.id,
            user_id=maya.id,
            title="Best way to visualize Dijkstra's algorithm?",
            content="I keep mixing up visited nodes and the priority queue. Does anyone have a good diagram or explanation?",
        )
        db.add(dijkstra_post)
        db.commit()
        db.refresh(dijkstra_post)

        practice_post = DiscussionPost(
            group_id=data_structures_squad.id,
            user_id=jordan.id,
            title="Practice problems for Friday",
            content="I uploaded a list of graph traversal problems. We can work through them before the session.",
        )
        db.add(practice_post)

        quiz_post = DiscussionPost(
            group_id=data_structures_squad.id,
            user_id=alex.id,
            title="Quiz 3 topics",
            content="Professor said BFS, DFS, adjacency lists, and runtime analysis will all be included.",
        )
        db.add(quiz_post)
        db.commit()

        db.add_all([
            DiscussionPost(
                group_id=data_structures_squad.id,
                user_id=jordan.id,
                parent_post_id=dijkstra_post.id,
                content="Try drawing the frontier as a min-heap.",
            ),
            DiscussionPost(
                group_id=data_structures_squad.id,
                user_id=taylor.id,
                parent_post_id=dijkstra_post.id,
                content="This animation helped me understand it.",
            ),
            DiscussionPost(
                group_id=data_structures_squad.id,
                user_id=alex.id,
                parent_post_id=dijkstra_post.id,
                content="I can demo it during today's session.",
            ),
        ])
        db.commit()

        notifications = [
            Notification(
                user_id=alex.id,
                message="Calculus Crew scheduled \"Exam Review\" for today at 6:00 PM.",
            ),
            Notification(
                user_id=alex.id,
                message="New discussion reply in Data Structures Squad.",
            ),
            Notification(
                user_id=alex.id,
                message="Code Collective changed its meeting link.",
            ),
            Notification(
                user_id=alex.id,
                message="Python Project Sprint begins tomorrow at 4:30 PM.",
                is_read=True,
            ),
            Notification(
                user_id=alex.id,
                message="Taylor Kim joined Code Collective.",
                is_read=True,
            ),
        ]
        db.add_all(notifications)
        db.commit()

        print("Seeded demo data.")
        print("Log in with: alex.morgan@uncc.edu / password123")

finally:
    db.close()
