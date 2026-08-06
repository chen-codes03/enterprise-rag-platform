"""AI 应用效果评估指标。

- token_f1: 字符级 token F1（适配中文），衡量回答与参考答案的匹配度。
- accuracy: F1 达到阈值的比例。
- recall: 检索召回率（命中相关来源数 / 相关来源总数）。
- latency_stats: 响应延迟 p50/p95/mean。
"""
from __future__ import annotations

import re
import statistics


def _tokens(text: str) -> set[str]:
    """字符级 token（适配中文，连续 CJK 拆为单字）。"""
    return set(re.findall(r"\w", text.lower()))


def token_f1(pred: str, ref: str) -> float:
    """字符级 token F1。"""
    p = _tokens(pred)
    r = _tokens(ref)
    if not p or not r:
        return 0.0
    tp = len(p & r)
    if tp == 0:
        return 0.0
    precision = tp / len(p)
    recall = tp / len(r)
    return 2 * precision * recall / (precision + recall)


def accuracy(
    preds: list[str], refs: list[str], threshold: float = 0.5
) -> float:
    """回答准确率：F1 >= threshold 的比例。"""
    if not preds:
        return 0.0
    correct = sum(1 for p, r in zip(preds, refs) if token_f1(p, r) >= threshold)
    return correct / len(preds)


def recall(retrieved: list, relevant: list) -> float:
    """检索召回率。"""
    if not relevant:
        return 0.0
    rel_set = set(relevant)
    hit = sum(1 for x in retrieved if x in rel_set)
    return hit / len(rel_set)


def latency_stats(times: list[float]) -> dict:
    """响应延迟统计：p50/p95/mean（秒）。"""
    if not times:
        return {"p50": 0.0, "p95": 0.0, "mean": 0.0}
    s = sorted(times)

    def pct(p: float) -> float:
        idx = max(0, int(len(s) * p) - 1)
        return s[idx]

    return {"p50": pct(0.5), "p95": pct(0.95), "mean": statistics.mean(times)}
