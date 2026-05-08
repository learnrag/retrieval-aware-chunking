"""Tests for evaluation metrics."""

from chunker.evaluation.metrics import (
    context_recall,
    mrr,
    precision_at_k,
    recall_at_k,
)


def test_retrieval_metrics():
    retrieved = ["a", "b", "c"]
    relevant = {"b"}
    assert recall_at_k(retrieved, relevant, 3) == 1.0
    assert recall_at_k(retrieved, relevant, 1) == 0.0
    assert precision_at_k(retrieved, relevant, 3) == 1 / 3
    assert mrr(retrieved, relevant) == 0.5


def test_context_recall():
    assert context_recall(["Backups every 6 hours."], ["every 6 hours"]) == 1.0
    assert context_recall(["unrelated"], ["every 6 hours"]) == 0.0
