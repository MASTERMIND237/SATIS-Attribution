def _create_student(client, email="john@example.com"):
    response = client.post(
        "/api/v1/students/",
        json={"last_name": "Doe", "first_name": "John", "email": email},
    )
    return response.json()


def _create_widget(client, name):
    response = client.post(
        "/api/v1/widgets/",
        json={"name": name, "description": f"Description de {name}"},
    )
    return response.json()


def test_assign_widgets_returns_unique_widgets(client):
    student = _create_student(client)
    _create_widget(client, "Container")
    _create_widget(client, "Text")
    _create_widget(client, "Row")

    response = client.post(
        f"/api/v1/assignments/assign?student_id={student['id']}",
        json={"widget_count": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert len({item["widget_id"] for item in body}) == 2


def test_assign_widgets_fails_when_student_already_has_assignments(client):
    student = _create_student(client)
    _create_widget(client, "Container")
    _create_widget(client, "Text")

    first_response = client.post(
        f"/api/v1/assignments/assign?student_id={student['id']}",
        json={"widget_count": 2},
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f"/api/v1/assignments/assign?student_id={student['id']}",
        json={"widget_count": 2},
    )
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Cet étudiant a déjà des widgets attribués"


def test_assign_widgets_reports_exhaustion(client):
    student = _create_student(client)
    _create_widget(client, "Container")

    response = client.post(
        f"/api/v1/assignments/assign?student_id={student['id']}",
        json={"widget_count": 2},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Plus aucun widget disponible. Veuillez contacter l'enseignant."
