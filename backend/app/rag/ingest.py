"""文档入库管道。

编排：文档解析（loaders）→ 文本分块（splitters）→ 向量库存储（vectorstore）。
"""
from __future__ import annotations

import json
import logging

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.models.base import Message, ModelProvider
from app.rag.loaders import load_document
from app.rag.splitters import split_documents
from app.rag.vectorstore import get_vectorstore

logger = logging.getLogger(__name__)


def ingest_documents(
    documents: list[Document],
    store: Chroma | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> int:
    """将文档分块后写入向量库，返回入库块数。"""
    chunks = split_documents(documents, chunk_size, chunk_overlap)
    store = store or get_vectorstore()
    store.add_documents(chunks)
    return len(chunks)


def ingest_file(
    path: str | Path,
    store: Chroma | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    source_name: str | None = None,
) -> int:
    """解析单个文件并入库，返回入库块数。

    source_name：可选的原始文件名，用于覆盖 metadata.source，
    避免上传场景下溯源来源显示为临时文件路径。未提供时沿用 path。
    """
    documents = load_document(path)
    if source_name:
        for doc in documents:
            doc.metadata["source"] = source_name
    return ingest_documents(documents, store, chunk_size, chunk_overlap)


# Prompt template for generating suggested questions from document content
_SUGGESTED_QUESTIONS_PROMPT = """根据以下企业文档内容，生成 3 个用户最可能会问的问题。

要求：
1. 问题要具体，基于文档中的实际内容
2. 不要出现"根据文档"之类的词
3. 仅输出 JSON 数组格式，不要任何其他文字
4. 如果文档内容不足以生成有意义的问题，返回空数组 []

格式示例：["报销流程是什么？", "年假怎么申请？", "考勤制度有哪些？"]

文档内容：
{content}"""


def generate_suggested_questions(
    text: str,
    provider: ModelProvider,
    max_chars: int = 2000,
) -> list[str]:
    """根据文档文本生成推荐问题。

    取前 max_chars 字符作为上下文，调用 LLM 生成 3 个推荐问题。
    失败时返回空列表，不阻断主流程。
    """
    if not text or not text.strip():
        return []

    snippet = text[:max_chars].strip()
    prompt = _SUGGESTED_QUESTIONS_PROMPT.format(content=snippet)

    try:
        result = provider.chat([Message(role="human", content=prompt)])
        raw = result.content.strip()
        # 兼容 LLM 可能包裹 ```json ... ``` 的情况
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        questions = json.loads(raw)
        if isinstance(questions, list):
            return [str(q) for q in questions if str(q).strip()]
        return []
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("生成推荐问题失败: %s", e)
        return []


def _meta_dir(uploads_dir: str | Path) -> Path:
    """推荐问题元数据存储目录：uploads_dir/.meta/"""
    meta_dir = Path(uploads_dir) / ".meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    return meta_dir


def _meta_path(uploads_dir: str | Path, filename: str) -> Path:
    """单个文档的推荐问题元数据文件路径。

    文件名中的特殊字符（路径分隔符等）替换为下划线，保证落到单文件。
    """
    safe_name = filename.replace("/", "_").replace("\\", "_")
    return _meta_dir(uploads_dir) / f"{safe_name}.json"


def save_suggested_questions(
    uploads_dir: str | Path,
    filename: str,
    questions: list[str],
) -> None:
    """将推荐问题持久化到独立 JSON 文件（与原始文件同名，位于 .meta/ 下）。

    采用独立文件而非向量库 metadata，原因：
      - Chroma 的 langchain 封装未暴露仅更新 metadata 的公开 API
      - 独立文件更健壮：向量库重建/迁移不会丢失推荐问题
    """
    try:
        path = _meta_path(uploads_dir, filename)
        path.write_text(
            json.dumps({"suggested_questions": questions}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("写入推荐问题元数据失败: %s", e)


def load_suggested_questions(
    uploads_dir: str | Path,
    filename: str,
) -> list[str]:
    """读取指定文档的推荐问题，不存在时返回空列表。"""
    try:
        path = _meta_path(uploads_dir, filename)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        questions = data.get("suggested_questions", [])
        return [str(q) for q in questions if str(q).strip()]
    except Exception:
        return []


def delete_suggested_questions(
    uploads_dir: str | Path,
    filename: str,
) -> None:
    """删除指定文档的推荐问题元数据文件（文档删除时调用）。"""
    try:
        path = _meta_path(uploads_dir, filename)
        if path.exists():
            path.unlink()
    except Exception as e:
        logger.warning("删除推荐问题元数据失败: %s", e)
