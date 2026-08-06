"""API 测试公共 fixture：注入 FakeLLM 链路与覆盖依赖。"""
import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from app.api.deps import get_rag_chain, get_store
from app.cache.qa_cache import QACache
from app.config import get_settings
from app.main import create_app
from app.models.deepseek import DeepSeekProvider
from app.rag.chain import RAGChain


@pytest.fixture
def api_client(kb_store, redis_client, monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    get_settings.cache_clear()

    provider = DeepSeekProvider(
        llm=FakeMessagesListChatModel(responses=[AIMessage(content="测试回答")])
    )
    chain = RAGChain(
        store=kb_store,
        model_provider=provider,
        top_k=3,
        qa_cache=QACache(redis_client),
    )

    app = create_app()
    app.dependency_overrides[get_rag_chain] = lambda: chain
    app.dependency_overrides[get_store] = lambda: kb_store

    with TestClient(app) as client:
        yield client
