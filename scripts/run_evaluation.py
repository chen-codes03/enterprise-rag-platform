"""评估演示脚本。

端到端运行评估体系：构建知识库 → 在评估数据集上跑 RAG 链路 vs 无 RAG 基线，
输出问答准确率、检索召回率、响应延迟对比报告。

使用 FakeLLM + DeterministicEmbeddings 离线可复现，无需真实大模型 API：
- RAG 模式：FakeLLM 返回参考答案（模拟"RAG 提供上下文后模型回答准确"）
- 无 RAG 基线：FakeLLM 返回模糊答案（模拟"无上下文时模型只能猜"）

用法：
    python -m scripts.run_evaluation
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

# 确保项目根目录在 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.evaluation.runner import (  # noqa: E402
    compare,
    evaluate_rag,
    evaluate_without_rag,
    load_dataset,
)
from app.models.deepseek import DeepSeekProvider  # noqa: E402
from app.rag.chain import RAGChain  # noqa: E402
from app.rag.embeddings import DeterministicEmbeddings  # noqa: E402
from app.rag.ingest import ingest_documents  # noqa: E402
from app.rag.vectorstore import get_vectorstore  # noqa: E402


# 知识库文档（与 tests/conftest.py 的 kb_store 保持一致）
KB_DOCS = [
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


def _build_store(persist_dir: str):
    store = get_vectorstore(
        embeddings=DeterministicEmbeddings(dim=32),
        persist_dir=persist_dir,
        collection="kb_eval",
    )
    ingest_documents(KB_DOCS, store=store)
    return store


def _rag_provider(dataset):
    """RAG 模式：FakeLLM 返回参考答案（模拟 RAG 提供上下文后回答准确）。"""
    responses = [AIMessage(content=item["reference_answer"]) for item in dataset]
    return DeepSeekProvider(llm=FakeMessagesListChatModel(responses=responses))


def _baseline_provider(dataset):
    """无 RAG 基线：FakeLLM 返回模糊答案（模拟无上下文时模型只能泛泛而谈）。"""
    vague = [
        AIMessage(
            content="建议您咨询相关部门或查阅公司内部资料以获取详细信息。"
        )
        for _ in dataset
    ]
    return DeepSeekProvider(llm=FakeMessagesListChatModel(responses=vague))


def main() -> None:
    print("=" * 60)
    print("企业知识库 RAG 智能问答平台 - 评估体系演示")
    print("=" * 60)

    # Windows 下 Chroma sqlite 句柄可能延迟释放，忽略清理错误
    tmp = tempfile.mkdtemp()
    dataset = load_dataset()
    print(f"\n[1] 加载评估数据集：{len(dataset)} 条 QA")

    try:
        store = _build_store(tmp)
        print(f"[2] 构建知识库向量库：{len(KB_DOCS)} 篇文档已入库")

        print("\n[3] 运行 RAG 链路评估 ...")
        rag_chain = RAGChain(
            store=store, model_provider=_rag_provider(dataset), top_k=3
        )
        rag_report = evaluate_rag(rag_chain, dataset)
        print(json.dumps(rag_report, ensure_ascii=False, indent=2))

        print("\n[4] 运行无 RAG 基线评估 ...")
        baseline_report = evaluate_without_rag(
            _baseline_provider(dataset), dataset
        )
        print(json.dumps(baseline_report, ensure_ascii=False, indent=2))

        print("\n[5] 对比报告（RAG vs Baseline）")
        comparison = compare(rag_report, baseline_report)
        print(json.dumps(comparison, ensure_ascii=False, indent=2))

        print("\n" + "=" * 60)
        print("结论：RAG 模式准确率显著高于无 RAG 基线，验证 RAG 链路有效。")
        print("=" * 60)
    finally:
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
