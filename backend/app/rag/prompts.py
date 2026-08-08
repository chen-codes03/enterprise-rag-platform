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
- 必须在引用每条信息的句子末尾标注来源编号，格式为 [1]、[2] 等，编号对应上下文中的 [1]、[2]。
- 例如：报销需在 7 个工作日内提交申请 [1]，财务部 5 个工作日内打款 [2]。
- 若信息来自同一来源，只需标注一次该来源编号。
"""


def get_rag_prompt() -> ChatPromptTemplate:
    """返回 RAG 对话 prompt 模板。"""
    return ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
