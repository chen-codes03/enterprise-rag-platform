"""T5.11: 健康检查测试。"""


def test_health_no_auth_required(api_client):
    r = api_client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "app" in data
