"""
Unit tests: notifications (GET/PUT /notifications/...).
"""

from conftest import create_group, register_user


def test_get_notifications_for_unknown_user_is_rejected(client):
    response = client.get("/notifications/999")
    assert response.status_code == 404


def test_get_notifications_returns_all_for_user(client):
    creator = register_user(client, email="creator@uncc.edu")
    member = register_user(client, email="member@uncc.edu")
    group = create_group(client, creator["id"], course_code="ITIS-3300")

    client.post(f"/study-groups/{group['id']}/members/{member['id']}")

    response = client.get(f"/notifications/{creator['id']}")
    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    assert notifications[0]["is_read"] is False


def test_mark_single_notification_read(client):
    creator = register_user(client, email="creator@uncc.edu")
    member = register_user(client, email="member@uncc.edu")
    group = create_group(client, creator["id"])
    client.post(f"/study-groups/{group['id']}/members/{member['id']}")

    notification = client.get(f"/notifications/{creator['id']}").json()[0]

    response = client.put(f"/notifications/{notification['id']}/read")
    assert response.status_code == 200
    assert response.json()["is_read"] is True

    refreshed = client.get(f"/notifications/{creator['id']}").json()[0]
    assert refreshed["is_read"] is True


def test_mark_all_notifications_read(client):
    creator = register_user(client, email="creator@uncc.edu")
    member_one = register_user(client, email="one@uncc.edu")
    member_two = register_user(client, email="two@uncc.edu")
    group = create_group(client, creator["id"])

    client.post(f"/study-groups/{group['id']}/members/{member_one['id']}")
    client.post(f"/study-groups/{group['id']}/members/{member_two['id']}")

    response = client.post(f"/notifications/{creator['id']}/read-all")
    assert response.status_code == 200
    assert all(n["is_read"] for n in response.json())

    dashboard = client.get(f"/dashboard/{creator['id']}").json()
    assert dashboard["stats"]["unread_updates"] == 0
