"""T5.1 RED: API Key 鉴权测试。"""
_HEADERS = {"X-API-Key": "test-key"}


def test_chat_without_api_key_returns_401(api_client):
    r = api_client.post("/api/v1/chat", json={"question": "测试"})
    assert r.status_code == 401


def test_chat_with_invalid_api_key_returns_401(api_client):
    r = api_client.post(
        "/api/v1/chat",
        json={"question": "测试"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert r.status_code == 401


def test_chat_with_valid_api_key_returns_200(api_client):
    r = api_client.post(
        "/api/v1/chat", json={"question": "测试"}, headers=_HEADERS
    )
    assert r.status_code == 200


def test_documents_without_api_key_returns_401(api_client):
    r = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("a.md", b"x", "text/markdown")},
    )
    assert r.status_code == 401
