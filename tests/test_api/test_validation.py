"""T5.9 RED: 参数校验测试。"""
_HEADERS = {"X-API-Key": "test-key"}


def test_chat_empty_question_returns_422(api_client):
    r = api_client.post(
        "/api/v1/chat", json={"question": ""}, headers=_HEADERS
    )
    assert r.status_code == 422


def test_chat_missing_question_returns_422(api_client):
    r = api_client.post("/api/v1/chat", json={}, headers=_HEADERS)
    assert r.status_code == 422


def test_chat_question_too_long_returns_422(api_client):
    r = api_client.post(
        "/api/v1/chat",
        json={"question": "x" * 2001},
        headers=_HEADERS,
    )
    assert r.status_code == 422


def test_chat_invalid_body_returns_422(api_client):
    r = api_client.post(
        "/api/v1/chat", json={"unexpected": 1}, headers=_HEADERS
    )
    assert r.status_code == 422
