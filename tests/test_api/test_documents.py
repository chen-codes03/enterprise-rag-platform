"""T5.3 RED: 文档上传接口测试。"""
_HEADERS = {"X-API-Key": "test-key"}


def test_upload_markdown_triggers_ingest(api_client):
    content = "# 测试文档\n\n企业报销流程说明内容详细描述。" * 5
    r = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.md", content.encode("utf-8"), "text/markdown")},
        headers=_HEADERS,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["filename"] == "test.md"
    assert data["chunks"] > 0


def test_upload_unsupported_format_returns_400(api_client):
    r = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("a.txt", b"x", "text/plain")},
        headers=_HEADERS,
    )
    assert r.status_code == 400


def test_upload_then_query(api_client):
    """上传文档后应能检索到相关内容。"""
    content = "# 差旅制度\n\n员工出差需提前在OA系统提交差旅申请，由部门经理审批。"
    up = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("travel.md", content.encode("utf-8"), "text/markdown")},
        headers=_HEADERS,
    )
    assert up.status_code == 200
    assert up.json()["chunks"] > 0

    # 问答（FakeLLM 固定回复，但 sources 应来自检索）
    chat = api_client.post(
        "/api/v1/chat",
        json={"question": "出差流程"},
        headers=_HEADERS,
    )
    assert chat.status_code == 200
    sources = chat.json()["sources"]
    assert len(sources) >= 1


def test_upload_invalidates_qa_cache(api_client, redis_client):
    """上传文档后应失效问答缓存，避免返回基于旧知识库的过时答案。"""
    from app.cache.qa_cache import QACache

    cache = QACache(redis_client)
    # 预填充问答缓存
    cache.set("旧问题", {"answer": "旧答案", "sources": []})
    assert cache.get("旧问题") is not None
    assert len(list(redis_client.scan_iter("qa:*"))) >= 1

    # 上传文档
    content = "# 新制度\n\n新规章制度详细内容说明描述。" * 5
    up = api_client.post(
        "/api/v1/documents/upload",
        files={"file": ("new.md", content.encode("utf-8"), "text/markdown")},
        headers=_HEADERS,
    )
    assert up.status_code == 200

    # 上传后问答缓存应被清空
    assert cache.get("旧问题") is None
    assert len(list(redis_client.scan_iter("qa:*"))) == 0
