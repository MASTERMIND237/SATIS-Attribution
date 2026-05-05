def test_create_student_and_reject_duplicate_email(client):
    payload = {
        "last_name": "Doe",
        "first_name": "Jane",
        "email": "jane@example.com",
    }

    response = client.post("/api/v1/students/", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["id"] > 0

    duplicate_response = client.post("/api/v1/students/", json=payload)
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Un étudiant avec cet email existe déjà"
