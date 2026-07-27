"""
Unit tests: study groups (POST/GET /study-groups/).
"""

from conftest import create_group, register_user


def test_create_study_group_success(client):
    user = register_user(client)

    response = client.post(
        "/study-groups/",
        json={
            "group_name": "Database Systems",
            "course_code": "itis-3300",
            "description": "Weekly review sessions.",
            "creator_user_id": user["id"],
            "status": "open",
            "max_members": 10,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["group_name"] == "Database Systems"
    # course codes are normalized to uppercase
    assert body["course_code"] == "ITIS-3300"
    assert body["creator_user_id"] == user["id"]


def test_create_study_group_invalid_max_members_is_rejected(client):
    user = register_user(client)

    response = client.post(
        "/study-groups/",
        json={
            "group_name": "Database Systems",
            "course_code": "ITIS-3300",
            "creator_user_id": user["id"],
            "max_members": 0,
        },
    )

    assert response.status_code == 400


def test_create_study_group_unknown_creator_is_rejected(client):
    response = client.post(
        "/study-groups/",
        json={
            "group_name": "Database Systems",
            "course_code": "ITIS-3300",
            "creator_user_id": 999,
            "max_members": 10,
        },
    )

    assert response.status_code == 404


def test_search_study_groups_by_course_code(client):
    user = register_user(client)
    create_group(client, user["id"], course_code="ITIS-3300")
    create_group(client, user["id"], group_name="Calculus II", course_code="MATH-1242")

    response = client.get("/study-groups/", params={"course_code": "itis"})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["course_code"] == "ITIS-3300"


def test_get_study_group_not_found(client):
    response = client.get("/study-groups/999")
    assert response.status_code == 404
