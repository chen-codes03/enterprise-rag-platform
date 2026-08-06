"""T6.4 RED: 评估运行器测试。"""
from langchain_core.language_models.fake_chat_models import (
    FakeMessagesListChatModel,
)
from langchain_core.messages import AIMessage

from app.evaluation.runner import (
    compare,
    evaluate_rag,
    evaluate_without_rag,
    load_dataset,
)
from app.models.deepseek import DeepSeekProvider
from app.rag.chain import RAGChain


def _provider_with_reference_answers(dataset):
    """让 FakeLLM 按序返回参考答案，验证准确率计算。"""
    responses = [AIMessage(content=item["reference_answer"]) for item in dataset]
    return DeepSeekProvider(llm=FakeMessagesListChatModel(responses=responses))


def test_load_dataset_has_items():
    ds = load_dataset()
    assert len(ds) >= 5
    assert all("question" in item and "reference_answer" in item for item in ds)


def test_evaluate_rag_returns_full_report(kb_store):
    ds = load_dataset()
    chain = RAGChain(
        store=kb_store, model_provider=_provider_with_reference_answers(ds), top_k=3
    )
    report = evaluate_rag(chain, ds)

    assert report["mode"] == "rag"
    assert report["n"] == len(ds)
    # FakeLLM 返回参考答案 → 准确率应为 1.0
    assert report["answer_accuracy"] == 1.0
    assert 0.0 <= report["retrieval_recall"] <= 1.0
    assert set(report["latency"].keys()) == {"p50", "p95", "mean"}
    assert report["latency"]["p50"] >= 0


def test_evaluate_without_rag(kb_store):
    ds = load_dataset()
    provider = _provider_with_reference_answers(ds)
    report = evaluate_without_rag(provider, ds)

    assert report["mode"] == "no_rag"
    assert report["n"] == len(ds)
    assert report["answer_accuracy"] == 1.0
    assert report["retrieval_recall"] == 0.0


def test_compare_improvement():
    import pytest

    rag = {"answer_accuracy": 0.8}
    baseline = {"answer_accuracy": 0.45}
    c = compare(rag, baseline)
    assert c["improvement"] == pytest.approx(0.35)
    assert c["rag_accuracy"] == 0.8
    assert c["baseline_accuracy"] == 0.45
