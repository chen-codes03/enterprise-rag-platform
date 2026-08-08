"""LLM 打分重排序器。

用现有 LLM provider 对向量检索召回的候选文档逐一打分，
按相关性排序后取 top-k，提升最终答案质量。

设计决策：选用 LLM 打分而非本地 cross-encoder，原因：
  - 零新依赖（复用现有 DeepSeek provider）
  - 零新 API Key
  - LLM 具备深层语义理解能力，比纯向量相似度更精准
  - 异常时自动 fallback 到原始向量检索顺序
"""
from __future__ import annotations

import json
import logging

from langchain_core.documents import Document

from app.models.base import Message, ModelProvider

logger = logging.getLogger(__name__)

_RERANK_PROMPT = """你是一个文档相关性评估专家。请为每个文档片段打分（0-10），判断其与查询的相关性。
10 分表示完全相关，0 分表示完全无关。

查询：{query}

文档片段：
{docs}

请仅输出 JSON 数组，每个元素为 {{"index": 片段编号, "score": 分数}}，不要输出任何其他内容。
格式示例：[{{"index": 1, "score": 8.5}}, {{"index": 2, "score": 3.0}}]
"""


def rerank(
    query: str,
    docs: list[Document],
    provider: ModelProvider,
    top_k: int,
) -> list[Document]:
    """对候选文档用 LLM 打分重排，返回 top-k。

    异常时 fallback 返回原始 docs[:top_k]，不阻断问答主流程。
    """
    if not docs or len(docs) <= top_k:
        return docs[:top_k]

    # 构建带编号的文档列表文本（截断每个片段避免 token 过长）
    parts: list[str] = []
    for i, doc in enumerate(docs, 1):
        snippet = doc.page_content[:500].strip()
        parts.append(f"[{i}] {snippet}")
    docs_text = "\n\n".join(parts)

    prompt = _RERANK_PROMPT.format(query=query, docs=docs_text)

    try:
        result = provider.chat([Message(role="human", content=prompt)])
        raw = result.content.strip()

        # 兼容 LLM 可能包裹 ```json ... ``` 的情况
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        scores = json.loads(raw)
        if not isinstance(scores, list):
            raise ValueError("LLM 返回的不是 JSON 数组")

        # 解析 {index, score} 并按 score 降序排序
        scored: list[tuple[int, float]] = []
        for item in scores:
            if isinstance(item, dict):
                idx = int(item.get("index", 0))
                score = float(item.get("score", 0))
                if 1 <= idx <= len(docs):
                    scored.append((idx, score))

        if not scored:
            raise ValueError("未解析到有效评分")

        scored.sort(key=lambda x: x[1], reverse=True)
        reranked = [docs[idx - 1] for idx, _ in scored[:top_k]]
        logger.info("重排序完成: %d 候选 -> %d 精选", len(docs), len(reranked))
        return reranked

    except Exception as e:
        logger.warning("LLM 重排序失败，fallback 到原始顺序: %s", e)
        return docs[:top_k]
