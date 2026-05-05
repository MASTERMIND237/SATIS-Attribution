def _create_student(client, first_name, email):
    response = client.post(
        "/api/v1/students/",
        json={"last_name": "SATIS", "first_name": first_name, "email": email},
    )
    return response.json()


def test_feedback_can_be_created_updated_and_cleared(client):
    student = _create_student(client, "Alice", "alice@example.com")

    create_response = client.put(
        f"/api/v1/feedback/students/{student['id']}",
        json={"reaction": "like"},
    )
    assert create_response.status_code == 200
    assert create_response.json()["reaction"] == "like"

    update_response = client.put(
        f"/api/v1/feedback/students/{student['id']}",
        json={"reaction": "dislike"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["reaction"] == "dislike"

    clear_response = client.put(
        f"/api/v1/feedback/students/{student['id']}",
        json={"reaction": "none"},
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["reaction"] is None


def test_admin_feedback_endpoints_show_counts_and_students(client):
    alice = _create_student(client, "Alice", "alice@example.com")
    bob = _create_student(client, "Bob", "bob@example.com")

    client.put(f"/api/v1/feedback/students/{alice['id']}", json={"reaction": "like"})
    client.put(f"/api/v1/feedback/students/{bob['id']}", json={"reaction": "dislike"})

    summary_response = client.get("/api/v1/feedback/admin/summary")
    assert summary_response.status_code == 200
    assert summary_response.json() == {
        "question": "Notre plateforme vous a t'elle ete utile ?",
        "total_students": 2,
        "likes": 1,
        "dislikes": 1,
        "no_response": 0,
    }

    responses_response = client.get("/api/v1/feedback/admin/responses")
    assert responses_response.status_code == 200
    reactions = {item["email"]: item["reaction"] for item in responses_response.json()}
    assert reactions == {
        "alice@example.com": "like",
        "bob@example.com": "dislike",
    }
