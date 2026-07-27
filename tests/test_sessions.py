"""
Unit tests: study sessions (POST /study-groups/{id}/sessions).
"""

from datetime import datetime, timedelta

from conftest import create_group, register_user


def future_iso(hours=24):
    return (datetime.now() + timedelta(hours=hours)).isoformat()


def test_create_session_success(client):
    creator = register_user(client)
    group = create_group(client, creator["id"])

    response = client.post(
        f"/study-groups/{group['id']}/sessions",
        json={
            "title": "Midterm review",
            "location": "Atkins Library",
            "scheduled_at": future_iso(),
            "duration_minutes": 90,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Midterm review"
    assert body["group_id"] == group["id"]


def test_create_session_invalid_duration_is_rejected(client):
    creator = register_user(client)
    group = create_group(client, creator["id"])

    response = client.post(
        f"/study-groups/{group['id']}/sessions",
        json={
            "title": "Midterm review",
            "scheduled_at": future_iso(),
            "duration_minutes": 0,
        },
    )

    assert response.status_code == 400


def test_create_session_for_unknown_group_is_rejected(client):
    response = client.post(
        "/study-groups/999/sessions",
        json={
            "title": "Midterm review",
            "scheduled_at": future_iso(),
            "duration_minutes": 60,
        },
    )

    assert response.status_code == 404


def test_create_session_notifies_group_members(client):
    creator = register_user(client, email="creator@uncc.edu")
    member = register_user(client, email="member@uncc.edu")
    group = create_group(client, creator["id"])
    client.post(f"/study-groups/{group['id']}/members/{member['id']}")

    client.post(
        f"/study-groups/{group['id']}/sessions",
        json={
            "title": "Midterm review",
            "scheduled_at": future_iso(),
            "duration_minutes": 60,
        },
    )

    dashboard = client.get(f"/dashboard/{member['id']}").json()
    messages = [n["message"] for n in dashboard["notifications"]]
    assert any("Midterm review" in m for m in messages)
