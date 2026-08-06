"""T3.11: 溯源测试。验证 sources 与检索结果一一对应，可映射回原文。"""
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from app.models.deepseek import DeepSeekProvider
from app.rag.chain import RAGChain


def test_sources_match_retrieve_output(kb_store):
    """ask 返回的 sources 内容应与 retrieve 输出一致（溯源完整性）。"""
    provider = DeepSeekProvider(
        llm=FakeMessagesListChatModel(responses=[AIMessage(content="回答")])
    )
    chain = RAGChain(store=kb_store, model_provider=provider, top_k=3)

    retrieved = chain.retrieve("报销")
    result = chain.ask("报销")

    assert [s["content"] for s in result.sources] == [
        d.page_content for d in retrieved
    ]


def test_sources_indices_sequential(kb_store):
    provider = DeepSeekProvider(
        llm=FakeMessagesListChatModel(responses=[AIMessage(content="回答")])
    )
    chain = RAGChain(store=kb_store, model_provider=provider, top_k=3)
    result = chain.ask("流程")

    indices = [s["index"] for s in result.sources]
    assert indices == list(range(1, len(indices) + 1))


def test_sources_content_traceable_to_kb(kb_store):
    """每条 source 内容应能在知识库已知文档中找到。"""
    kb_contents = {
        "企业报销流程：员工在OA系统提交报销单并附发票，经部门经理审批后交财务打款。",
        "请假流程：员工在考勤系统提交请假申请，3天以内由直属主管审批，3天以上需HR审批。",
        "新员工入职第一天需到HR领取工牌、办理门禁卡，并由IT开通邮箱与系统账号。",
        "服务器部署流程：编写Dockerfile构建镜像，使用docker compose编排app与redis服务一键启动。",
    }
    provider = DeepSeekProvider(
        llm=FakeMessagesListChatModel(responses=[AIMessage(content="回答")])
    )
    chain = RAGChain(store=kb_store, model_provider=provider, top_k=4)
    result = chain.ask("任意问题")

    for s in result.sources:
        assert s["content"] in kb_contents
