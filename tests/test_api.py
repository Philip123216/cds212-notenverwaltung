def test_list_is_empty_initially(client):
    response = client.get("/api/grades")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_grade_success(client):
    payload = {"course": "DevOps", "grade": 5.5, "ects": 4}
    response = client.post("/api/grades", json=payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body["course"] == "DevOps"
    assert body["grade"] == 5.5
    assert body["ects"] == 4
    assert isinstance(body["id"], int)


def test_get_single_grade(client):
    created = client.post(
        "/api/grades", json={"course": "Mathe", "grade": 4.5, "ects": 6}
    ).get_json()
    response = client.get(f"/api/grades/{created['id']}")
    assert response.status_code == 200
    assert response.get_json() == created


def test_get_unknown_grade_returns_404(client):
    assert client.get("/api/grades/999").status_code == 404


def test_delete_grade(client):
    created = client.post(
        "/api/grades", json={"course": "Temp", "grade": 5.0, "ects": 2}
    ).get_json()
    assert client.delete(f"/api/grades/{created['id']}").status_code == 204
    assert client.get("/api/grades").get_json() == []


def test_delete_unknown_grade_returns_404(client):
    assert client.delete("/api/grades/999").status_code == 404


def test_gpa_on_empty_list_returns_zero(client):
    res = client.get("/api/grades/gpa").get_json()
    assert res == {"gpa": 0.0, "total_ects": 0, "count": 0}


def test_gpa_calculation_weighted(client):
    # DevOps: 5.5 * 4 ECTS = 22.0
    client.post("/api/grades", json={"course": "DevOps", "grade": 5.5, "ects": 4})
    # Informatik: 4.0 * 6 ECTS = 24.0
    # Summe: 46.0 / 10 ECTS = 4.6 GPA
    client.post("/api/grades", json={"course": "Informatik", "grade": 4.0, "ects": 6})

    res = client.get("/api/grades/gpa").get_json()
    assert res["gpa"] == 4.6
    assert res["total_ects"] == 10
    assert res["count"] == 2


# --- Validierungsprüfungen (Grenzfälle) ---


def test_invalid_grade_too_high(client):
    res = client.post("/api/grades", json={"course": "Test", "grade": 6.5, "ects": 3})
    assert res.status_code == 400
    assert "between 1.0 and 6.0" in res.get_json()["error"]


def test_invalid_grade_too_low(client):
    res = client.post("/api/grades", json={"course": "Test", "grade": 0.5, "ects": 3})
    assert res.status_code == 400


def test_invalid_ects_negative(client):
    res = client.post("/api/grades", json={"course": "Test", "grade": 5.0, "ects": -2})
    assert res.status_code == 400


def test_empty_course_name_rejected(client):
    res = client.post("/api/grades", json={"course": "   ", "grade": 5.0, "ects": 3})
    assert res.status_code == 400
