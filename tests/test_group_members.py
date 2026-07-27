"""
Unit tests: group membership (join/leave) and the notifications
that joining is supposed to generate.
"""

from conftest import create_group, register_user


def test_join_group_success(client):
    creator = register_user(client, email="creator@uncc.edu")
    member = register_user(client, email="member@uncc.edu")
    group = create_group(client, creator["id"])

    response = client.post(f"/study-groups/{group['id']}/members/{member['id']}")

    assert response.status_code == 201

    members = client.get(f"/study-groups/{group['id']}/members").json()
    member_ids = {m["user_id"] for m in members}
    assert member["id"] in member_ids


def test_join_group_creates_notification_for_creator(client):
    creator = register_user(client, email="creator@uncc.edu")
    member = register_user(client, email="member@uncc.edu", display_name="Jacob Miller")
    group = create_group(client, creator["id"], course_code="ITIS-3300")

    client.post(f"/study-groups/{group['id']}/members/{member['id']}")

    dashboard = client.get(f"/dashboard/{creator['id']}").json()
    messages = [n["message"] for n in dashboard["notifications"]]
    assert any("Jacob Miller joined ITIS-3300" in m for m in messages)


def test_join_group_twice_is_rejected(client):
    creator = register_user(client, email="creator@uncc.edu")
    member = register_user(client, email="member@uncc.edu")
    group = create_group(client, creator["id"])

    first = client.post(f"/study-groups/{group['id']}/members/{member['id']}")
    second = client.post(f"/study-groups/{group['id']}/members/{member['id']}")

    assert first.status_code == 201
    assert second.status_code == 409


def test_join_full_group_is_rejected(client):
    creator = register_user(client, email="creator@uncc.edu")
    group = create_group(client, creator["id"], max_members=1)

    # creator does not auto-join, so the first join should succeed...
    member_one = register_user(client, email="one@uncc.edu")
    first = client.post(f"/study-groups/{group['id']}/members/{member_one['id']}")
    assert first.status_code == 201

    # ...and the group is now full (max_members=1)
    member_two = register_user(client, email="two@uncc.edu")
    second = client.post(f"/study-groups/{group['id']}/members/{member_two['id']}")
    assert second.status_code == 409
    assert "full" in second.json()["detail"].lower()


def test_leave_group_success(client):
    creator = register_user(client, email="creator@uncc.edu")
    member = register_user(client, email="member@uncc.edu")
    group = create_group(client, creator["id"])

    client.post(f"/study-groups/{group['id']}/members/{member['id']}")
    response = client.delete(f"/study-groups/{group['id']}/members/{member['id']}")

    assert response.status_code == 204

    members = client.get(f"/study-groups/{group['id']}/members").json()
    assert all(m["user_id"] != member["id"] for m in members)


def test_leave_group_when_not_a_member_is_rejected(client):
    creator = register_user(client, email="creator@uncc.edu")
    non_member = register_user(client, email="outsider@uncc.edu")
    group = create_group(client, creator["id"])

    response = client.delete(f"/study-groups/{group['id']}/members/{non_member['id']}")

    assert response.status_code == 404
