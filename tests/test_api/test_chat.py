"""T5.5 RED: 同步问答接口测试。"""
_HEADERS = {"X-API-Key": "test-key"}


def test_chat_returns_answer_and_sources(api_client):
    r = api_client.post(
        "/api/v1/chat", json={"question": "如何报销"}, headers=_HEADERS
    )
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "测试回答"
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) >= 1
    assert "source" in data["sources"][0]
    assert "index" in data["sources"][0]


def test_chat_repeat_hits_cache(api_client, redis_client):
    """重复请求应命中缓存，返回一致结果。"""
    r1 = api_client.post(
        "/api/v1/chat", json={"question": "报销流程"}, headers=_HEADERS
    )
    r2 = api_client.post(
        "/api/v1/chat", json={"question": "报销流程"}, headers=_HEADERS
    )
    assert r1.status_code == r2.status_code == 200
    assert r1.json() == r2.json()
