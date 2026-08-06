"""T3.3 RED: RAG prompt 模板测试。"""
from langchain_core.prompts import ChatPromptTemplate

from app.rag.prompts import RAG_PROMPT_TEMPLATE, get_rag_prompt


def test_prompt_has_context_and_question_placeholders():
    assert "{context}" in RAG_PROMPT_TEMPLATE
    assert "{question}" in RAG_PROMPT_TEMPLATE


def test_prompt_guides_source_numbering():
    """prompt 应引导模型引用来源编号。"""
    assert "[1]" in RAG_PROMPT_TEMPLATE


def test_prompt_forbids_fabrication():
    """prompt 应要求不编造。"""
    assert "未找到" in RAG_PROMPT_TEMPLATE or "禁止编造" in RAG_PROMPT_TEMPLATE


def test_get_rag_prompt_returns_chat_prompt_template():
    p = get_rag_prompt()
    assert isinstance(p, ChatPromptTemplate)
