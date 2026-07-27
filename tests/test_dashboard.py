"""
Unit tests: dashboard aggregate endpoint (GET /dashboard/{user_id}).
"""

from datetime import datetime, timedelta

from conftest import create_group, register_user


def test_dashboard_for_unknown_user_is_rejected(client):
    response = client.get("/dashboard/999")
    assert response.status_code == 404


def test_dashboard_stats_reflect_activity(client):
    creator = register_user(client, email="creator@uncc.edu")
    member = register_user(client, email="member@uncc.edu")
    group = create_group(client, creator["id"], course_code="ITIS-3300")

    client.post(f"/study-groups/{group['id']}/members/{member['id']}")

    scheduled_at = (datetime.now() + timedelta(days=1)).isoformat()
    client.post(
        f"/study-groups/{group['id']}/sessions",
        json={"title": "Exam review", "scheduled_at": scheduled_at, "duration_minutes": 60},
    )

    client.post(
        f"/study-groups/{group['id']}/posts",
        json={"title": "Quiz topics", "content": "BFS, DFS, adjacency lists.", "user_id": creator["id"]},
    )

    dashboard = client.get(f"/dashboard/{creator['id']}").json()

    assert dashboard["stats"]["joined_groups"] == 1
    assert dashboard["stats"]["upcoming_sessions"] == 1
    assert dashboard["stats"]["discussion_posts"] == 1
    # creator has two unread notifications: member joined, and their own post
    # doesn't notify themselves, so only the join notification is unread here
    assert dashboard["stats"]["unread_updates"] >= 1


def test_dashboard_popular_groups_only_includes_open_groups(client):
    creator = register_user(client, email="creator@uncc.edu")
    create_group(client, creator["id"], group_name="Open Group", course_code="ITIS-1000")

    response = client.post(
        "/study-groups/",
        json={
            "group_name": "Full Group",
            "course_code": "ITIS-2000",
            "creator_user_id": creator["id"],
            "status": "full",
            "max_members": 5,
        },
    )
    assert response.status_code == 201

    dashboard = client.get(f"/dashboard/{creator['id']}").json()
    popular_names = [g["group_name"] for g in dashboard["popular_groups"]]
    assert "Open Group" in popular_names
    assert "Full Group" not in popular_names


def test_dashboard_recently_joined_limited_to_three(client):
    creator = register_user(client, email="creator@uncc.edu")
    for i in range(5):
        create_group(
            client,
            creator["id"],
            group_name=f"Group {i}",
            course_code=f"ITIS-{1000 + i}",
        )

    dashboard = client.get(f"/dashboard/{creator['id']}").json()
    assert len(dashboard["recently_joined"]) == 3
