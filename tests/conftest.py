"""全局 pytest fixtures。"""
import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """每个测试前后清除 get_settings 缓存，保证环境变量改动生效。"""
    from app.api.deps import clear_component_cache
    from app.config import get_settings

    get_settings.cache_clear()
    clear_component_cache()
    yield
    get_settings.cache_clear()
    clear_component_cache()


@pytest.fixture
def tmp_chroma_dir(tmp_path: Path) -> Path:
    """临时 Chroma 持久化目录，测试结束自动清理。"""
    d = tmp_path / "chroma"
    d.mkdir(exist_ok=True)
    yield d
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def isolated_env(monkeypatch):
    """提供一个干净环境，便于注入测试用环境变量。"""
    # 清除可能干扰的变量
    for key in list(os.environ.keys()):
        if key.startswith(("DEEPSEEK_", "QWEN_", "EMBEDDING_", "MODEL_")):
            monkeypatch.delenv(key, raising=False)
    return monkeypatch


@pytest.fixture
def redis_client():
    """基于 fakeredis 的 Redis 客户端，测试用，无需真实 Redis。"""
    import fakeredis

    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def kb_store(tmp_chroma_dir):
    """预置企业知识库向量库（DeterministicEmbeddings，离线可复现）。"""
    from langchain_core.documents import Document

    from app.rag.embeddings import DeterministicEmbeddings
    from app.rag.ingest import ingest_documents
    from app.rag.vectorstore import get_vectorstore

    store = get_vectorstore(
        embeddings=DeterministicEmbeddings(dim=32),
        persist_dir=str(tmp_chroma_dir),
        collection="kb_test",
    )
    docs = [
        Document(
            page_content="企业报销流程：员工在OA系统提交报销单并附发票，经部门经理审批后交财务打款。",
            metadata={"source": "财务制度.md", "section": "报销"},
        ),
        Document(
            page_content="请假流程：员工在考勤系统提交请假申请，3天以内由直属主管审批，3天以上需HR审批。",
            metadata={"source": "考勤制度.md", "section": "请假"},
        ),
        Document(
            page_content="新员工入职第一天需到HR领取工牌、办理门禁卡，并由IT开通邮箱与系统账号。",
            metadata={"source": "入职指南.md", "section": "入职"},
        ),
        Document(
            page_content="服务器部署流程：编写Dockerfile构建镜像，使用docker compose编排app与redis服务一键启动。",
            metadata={"source": "部署文档.md", "section": "部署"},
        ),
    ]
    ingest_documents(docs, store=store)
    return store
