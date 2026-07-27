"""
Unit tests: discussion posts, including threaded replies (parent_post_id).
"""

from conftest import create_group, register_user


def test_create_top_level_post_includes_author_name(client):
    creator = register_user(client, display_name="Maya Patel", email="maya@uncc.edu")
    group = create_group(client, creator["id"])

    response = client.post(
        f"/study-groups/{group['id']}/posts",
        json={
            "title": "Best way to visualize Dijkstra's algorithm?",
            "content": "I keep mixing up visited nodes and the priority queue.",
            "user_id": creator["id"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["author_name"] == "Maya Patel"
    assert body["parent_post_id"] is None


def test_create_reply_to_post(client):
    creator = register_user(client, display_name="Maya Patel", email="maya@uncc.edu")
    replier = register_user(client, display_name="Jordan Lee", email="jordan@uncc.edu")
    group = create_group(client, creator["id"])
    client.post(f"/study-groups/{group['id']}/members/{replier['id']}")

    post = client.post(
        f"/study-groups/{group['id']}/posts",
        json={
            "title": "Practice problems for Friday",
            "content": "I uploaded a list of graph traversal problems.",
            "user_id": creator["id"],
        },
    ).json()

    reply_response = client.post(
        f"/study-groups/{group['id']}/posts",
        json={
            "content": "Try drawing the frontier as a min-heap.",
            "user_id": replier["id"],
            "parent_post_id": post["id"],
        },
    )

    assert reply_response.status_code == 201
    reply = reply_response.json()
    assert reply["parent_post_id"] == post["id"]
    assert reply["author_name"] == "Jordan Lee"
    assert reply["title"] is None


def test_reply_to_post_in_wrong_group_is_rejected(client):
    creator = register_user(client, email="creator@uncc.edu")
    group_one = create_group(client, creator["id"], course_code="ITIS-3300")
    group_two = create_group(client, creator["id"], group_name="Calculus II", course_code="MATH-1242")

    post = client.post(
        f"/study-groups/{group_one['id']}/posts",
        json={"title": "Question", "content": "Details here.", "user_id": creator["id"]},
    ).json()

    reply_response = client.post(
        f"/study-groups/{group_two['id']}/posts",
        json={
            "content": "Wrong group reply attempt.",
            "user_id": creator["id"],
            "parent_post_id": post["id"],
        },
    )

    assert reply_response.status_code == 404


def test_get_group_posts_orders_oldest_first_and_includes_replies(client):
    creator = register_user(client, email="creator@uncc.edu")
    group = create_group(client, creator["id"])

    first = client.post(
        f"/study-groups/{group['id']}/posts",
        json={"title": "First post", "content": "...", "user_id": creator["id"]},
    ).json()
    client.post(
        f"/study-groups/{group['id']}/posts",
        json={"title": "Second post", "content": "...", "user_id": creator["id"]},
    )
    client.post(
        f"/study-groups/{group['id']}/posts",
        json={
            "content": "A reply to the first post.",
            "user_id": creator["id"],
            "parent_post_id": first["id"],
        },
    )

    posts = client.get(f"/study-groups/{group['id']}/posts").json()
    assert len(posts) == 3
    assert posts[0]["title"] == "First post"
    assert posts[1]["title"] == "Second post"
    assert posts[2]["parent_post_id"] == first["id"]
