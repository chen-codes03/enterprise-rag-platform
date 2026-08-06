"""T6.1 RED: 评估指标测试。验证 accuracy/recall/latency 计算正确。"""
from app.evaluation.metrics import accuracy, latency_stats, recall, token_f1


def test_token_f1_identical():
    assert token_f1("报销流程", "报销流程") == 1.0


def test_token_f1_no_overlap():
    assert token_f1("苹果", "香蕉") == 0.0


def test_token_f1_partial():
    f = token_f1("报销流程", "报销")
    assert 0.0 < f < 1.0


def test_accuracy_half():
    preds = ["报销流程", "完全无关的内容"]
    refs = ["报销流程", "其他答案"]
    assert accuracy(preds, refs) == 0.5


def test_accuracy_empty():
    assert accuracy([], []) == 0.0


def test_recall_full():
    assert recall(["a.md", "b.md"], ["a.md"]) == 1.0


def test_recall_partial():
    assert recall(["a.md"], ["a.md", "b.md"]) == 0.5


def test_recall_none():
    assert recall(["a.md"], []) == 0.0


def test_latency_stats_structure():
    times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    s = latency_stats(times)
    assert set(s.keys()) == {"p50", "p95", "mean"}
    assert s["mean"] == sum(times) / len(times)
    assert s["p50"] <= s["p95"]


def test_latency_stats_empty():
    s = latency_stats([])
    assert s == {"p50": 0.0, "p95": 0.0, "mean": 0.0}
