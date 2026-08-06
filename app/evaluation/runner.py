"""评估运行器。

在评估数据集上运行 RAG 链路（或无 RAG 基线），计算问答准确率、检索召回率、
响应延迟，用于持续优化 Prompt 与检索策略。
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from app.evaluation.metrics import accuracy, latency_stats, recall


def load_dataset(path: str | Path | None = None) -> list[dict]:
    """加载评估数据集。"""
    p = Path(path) if path else Path(__file__).parent / "dataset.json"
    return json.loads(p.read_text(encoding="utf-8"))


def evaluate_rag(chain, dataset: list[dict]) -> dict:
    """在数据集上评估 RAG 链路。"""
    preds: list[str] = []
    refs: list[str] = []
    latencies: list[float] = []
    recalls: list[float] = []

    for item in dataset:
        t0 = time.monotonic()
        result = chain.ask(item["question"])
        latencies.append(time.monotonic() - t0)
        preds.append(result.answer)
        refs.append(item["reference_answer"])
        retrieved_sources = [s["source"] for s in result.sources]
        recalls.append(recall(retrieved_sources, item.get("relevant_sources", [])))

    return {
        "mode": "rag",
        "n": len(dataset),
        "answer_accuracy": accuracy(preds, refs),
        "retrieval_recall": statistics.mean(recalls) if recalls else 0.0,
        "latency": latency_stats(latencies),
    }


def evaluate_without_rag(model_provider, dataset: list[dict]) -> dict:
    """无 RAG 基线：直接用大模型回答（无上下文）。"""
    from app.models.base import Message

    preds: list[str] = []
    refs: list[str] = []
    latencies: list[float] = []
    for item in dataset:
        t0 = time.monotonic()
        result = model_provider.chat(
            [Message(role="human", content=item["question"])]
        )
        latencies.append(time.monotonic() - t0)
        preds.append(result.content)
        refs.append(item["reference_answer"])
    return {
        "mode": "no_rag",
        "n": len(dataset),
        "answer_accuracy": accuracy(preds, refs),
        "retrieval_recall": 0.0,
        "latency": latency_stats(latencies),
    }


def compare(rag_report: dict, baseline_report: dict) -> dict:
    """对比 RAG 与基线的准确率提升。"""
    return {
        "rag_accuracy": rag_report["answer_accuracy"],
        "baseline_accuracy": baseline_report["answer_accuracy"],
        "improvement": rag_report["answer_accuracy"]
        - baseline_report["answer_accuracy"],
    }
