"""T5.7 RED: SSE 流式问答测试。"""
_HEADERS = {"X-API-Key": "test-key"}


def _parse_sse(text: str) -> tuple[list[dict], str]:
    """从 SSE 文本中提取 sources 事件与拼接后的回答。"""
    import json

    sources: list[dict] = []
    answer_parts: list[str] = []
    event = ""
    for line in text.split("\n"):
        if line.startswith("event: "):
            event = line[len("event: ") :].strip()
        elif line.startswith("data: "):
            payload = line[len("data: ") :]
            if event == "sources":
                sources = json.loads(payload)
                event = ""
            elif payload == "[DONE]":
                continue
            else:
                answer_parts.append(payload)
    return sources, "".join(answer_parts)


def test_chat_stream_returns_sse(api_client):
    with api_client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"question": "报销流程"},
        headers=_HEADERS,
    ) as r:
        assert r.status_code == 200
        text = r.read().decode("utf-8")

    assert "event: sources" in text
    assert "data: [DONE]" in text

    sources, answer = _parse_sse(text)
    assert len(sources) >= 1
    assert "source" in sources[0]
    assert "测试回答" in answer


def test_chat_stream_without_api_key_returns_401(api_client):
    r = api_client.post(
        "/api/v1/chat/stream", json={"question": "报销流程"}
    )
    assert r.status_code == 401
