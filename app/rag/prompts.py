"""RAG Prompt 模板。

引导模型严格基于上下文回答、引用来源编号、禁止编造。
"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT_TEMPLATE = """你是一个企业知识库智能助手。请严格基于以下检索到的上下文回答问题。
若上下文不足以回答，请直接说明"知识库中未找到相关信息"，禁止编造。

【上下文】
{context}

【问题】
{question}

【要求】
- 回答简洁准确，直接针对问题。
- 在引用信息处标注来源编号，如 [1]、[2]，对应上下文中的编号。
"""


def get_rag_prompt() -> ChatPromptTemplate:
    """返回 RAG 对话 prompt 模板。"""
    return ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
