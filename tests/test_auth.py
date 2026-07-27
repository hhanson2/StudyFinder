"""
Unit tests: authentication (POST /auth/register, POST /auth/login).
"""


def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={
            "display_name": "Darren Student",
            "email": "darren@uncc.edu",
            "password": "password123",
            "major": "Computer Science",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "darren@uncc.edu"
    assert body["user"]["display_name"] == "Darren Student"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_register_duplicate_email_is_rejected(client):
    payload = {
        "display_name": "Darren Student",
        "email": "darren@uncc.edu",
        "password": "password123",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"].lower()


def test_register_password_too_short_is_rejected(client):
    response = client.post(
        "/auth/register",
        json={
            "display_name": "Darren Student",
            "email": "darren@uncc.edu",
            "password": "abc",
        },
    )

    assert response.status_code == 400
    assert "6 characters" in response.json()["detail"]


def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "display_name": "Darren Student",
            "email": "darren@uncc.edu",
            "password": "password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": "darren@uncc.edu", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "darren@uncc.edu"


def test_login_wrong_password_is_rejected(client):
    client.post(
        "/auth/register",
        json={
            "display_name": "Darren Student",
            "email": "darren@uncc.edu",
            "password": "password123",
        },
    )

    response = client.post(
        "/auth/login",
        json={"email": "darren@uncc.edu", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_unknown_email_is_rejected(client):
    response = client.post(
        "/auth/login",
        json={"email": "nobody@uncc.edu", "password": "password123"},
    )

    assert response.status_code == 401
