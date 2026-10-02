def test_health_reports_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_ready_reports_ready(client):
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ready"


def test_ready_returns_503_when_unhealthy(app, client):
    class BrokenRepository:
        def healthy(self):
            return False

    app.extensions["repository"] = BrokenRepository()
    assert client.get("/ready").status_code == 503


def test_metrics_endpoint_is_exposed(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    assert b"notenverwaltung_info" in res.data
