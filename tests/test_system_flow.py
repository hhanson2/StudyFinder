"""
System (functional) test.

Unlike the unit tests in the other files -- which each check one endpoint in
isolation -- this test walks through a realistic end-to-end user journey that
touches every phase of the project: registration/login, searching, creating
and joining a group, scheduling a session, posting to the discussion board,
notifications, the dashboard aggregate view, and the profile stats. It is
meant to mirror how an actual user would move through the app in one sitting.
"""

from datetime import datetime, timedelta


def test_full_student_study_group_journey(client):
    # 1. Two students register.
    darren_resp = client.post(
        "/auth/register",
        json={
            "display_name": "Darren Student",
            "email": "darren@uncc.edu",
            "password": "password123",
            "major": "Computer Science",
        },
    )
    assert darren_resp.status_code == 201
    darren = darren_resp.json()["user"]

    jacob_resp = client.post(
        "/auth/register",
        json={
            "display_name": "Jacob Miller",
            "email": "jacob@uncc.edu",
            "password": "password123",
            "major": "Information Technology",
        },
    )
    assert jacob_resp.status_code == 201
    jacob = jacob_resp.json()["user"]

    # 2. Darren logs in.
    login_resp = client.post(
        "/auth/login",
        json={"email": "darren@uncc.edu", "password": "password123"},
    )
    assert login_resp.status_code == 200

    # 3. Darren searches for groups on his course -- there aren't any yet.
    search_resp = client.get("/study-groups/", params={"course_code": "ITIS-3300"})
    assert search_resp.status_code == 200
    assert search_resp.json() == []

    # 4. Darren creates a study group for that course.
    group_resp = client.post(
        "/study-groups/",
        json={
            "group_name": "Database Systems",
            "course_code": "ITIS-3300",
            "description": "Weekly review of SQL and normalization.",
            "creator_user_id": darren["id"],
            "status": "open",
            "max_members": 10,
        },
    )
    assert group_resp.status_code == 201
    group = group_resp.json()

    # 5. Now Jacob's search for the same course code finds it.
    search_resp = client.get("/study-groups/", params={"course_code": "3300"})
    assert search_resp.status_code == 200
    assert len(search_resp.json()) == 1
    assert search_resp.json()[0]["id"] == group["id"]

    # 6. Jacob joins the group.
    join_resp = client.post(f"/study-groups/{group['id']}/members/{jacob['id']}")
    assert join_resp.status_code == 201

    members_resp = client.get(f"/study-groups/{group['id']}/members")
    assert members_resp.status_code == 200
    assert len(members_resp.json()) == 1

    # 7. Darren, as the group's creator, sees a notification that Jacob joined.
    darren_dashboard = client.get(f"/dashboard/{darren['id']}").json()
    join_messages = [n["message"] for n in darren_dashboard["notifications"]]
    assert any("Jacob Miller joined ITIS-3300" in m for m in join_messages)

    # 8. Darren schedules a study session for the group.
    scheduled_at = (datetime.now() + timedelta(days=1)).isoformat()
    session_resp = client.post(
        f"/study-groups/{group['id']}/sessions",
        json={
            "title": "Midterm review",
            "location": "Atkins Library",
            "scheduled_at": scheduled_at,
            "duration_minutes": 90,
        },
    )
    assert session_resp.status_code == 201

    # 9. Jacob now sees the upcoming session on his dashboard, and a
    #    notification that it was scheduled.
    jacob_dashboard = client.get(f"/dashboard/{jacob['id']}").json()
    assert len(jacob_dashboard["upcoming_sessions"]) == 1
    assert jacob_dashboard["upcoming_sessions"][0]["title"] == "Midterm review"
    session_messages = [n["message"] for n in jacob_dashboard["notifications"]]
    assert any("Midterm review" in m for m in session_messages)

    # 10. Jacob posts a question to the group's discussion board.
    post_resp = client.post(
        f"/study-groups/{group['id']}/posts",
        json={
            "title": "Which chapters for the midterm?",
            "content": "Are chapters 1-5 all in scope?",
            "user_id": jacob["id"],
        },
    )
    assert post_resp.status_code == 201

    # 11. Darren sees a notification about the new discussion reply.
    darren_dashboard = client.get(f"/dashboard/{darren['id']}").json()
    post_messages = [n["message"] for n in darren_dashboard["notifications"]]
    assert any("New discussion reply" in m for m in post_messages)

    # 12. Both students' profile stats reflect their activity.
    darren_profile = client.get(f"/users/{darren['id']}/profile").json()
    assert darren_profile["stats"]["groups_created"] == 1
    assert darren_profile["stats"]["upcoming_sessions"] == 1

    jacob_profile = client.get(f"/users/{jacob['id']}/profile").json()
    assert jacob_profile["stats"]["groups_joined"] == 1
    assert jacob_profile["stats"]["discussion_posts"] == 1

    # 13. Jacob updates his profile in Settings.
    update_resp = client.put(
        f"/users/{jacob['id']}",
        json={
            "display_name": "Jacob Miller",
            "major": "Information Technology",
            "school_year": "Senior",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["school_year"] == "Senior"

    # 14. Jacob decides to leave the group before the session.
    leave_resp = client.delete(f"/study-groups/{group['id']}/members/{jacob['id']}")
    assert leave_resp.status_code == 204

    members_resp = client.get(f"/study-groups/{group['id']}/members")
    assert members_resp.status_code == 200
    assert len(members_resp.json()) == 0

    # 15. The session Darren created still exists and still belongs to him,
    #     independent of Jacob's membership.
    darren_sessions = client.get(f"/users/{darren['id']}/sessions").json()
    assert len(darren_sessions) == 1
    assert darren_sessions[0]["title"] == "Midterm review"
