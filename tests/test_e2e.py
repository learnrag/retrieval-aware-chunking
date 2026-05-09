"""End-to-end acceptance tests (mock embedder)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from chunker.embedding.mock import MockEmbedder
from chunker.pipeline import build_index, search

SAMPLE = """# Database Backups
Production databases are backed up every 6 hours.
Backups are retained for 30 days.
Restore requests require approval.
"""


def test_acceptance_parent_child(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "sample.md").write_text(SAMPLE, encoding="utf-8")
    index = tmp_path / "index"
    embedder = MockEmbedder(dimension=64, seed=0)

    build_index(
        data,
        index,
        embedder,
        strategy="parent_child",
        child_size_tokens=16,
        parent_size_tokens=128,
        overlap_tokens=2,
    )
    result = search(
        "How often are production databases backed up?",
        index,
        embedder,
        top_k=5,
        expansion="parent",
    )
    assert any("every 6 hours" in r.text for r in result.results)
    assert result.results[0].child_id
    assert result.expanded_context
    assert result.expanded_context[0].derived_from
    assert "score" in result.results[0].to_dict()

    # Deterministic re-run
    again = search(
        "How often are production databases backed up?",
        index,
        embedder,
        top_k=5,
        expansion="parent",
    )
    assert [r.child_id for r in again.results] == [r.child_id for r in result.results]


def test_acceptance_sentence_window(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "sample.md").write_text(SAMPLE, encoding="utf-8")
    index = tmp_path / "index"
    embedder = MockEmbedder(dimension=64, seed=0)
    build_index(data, index, embedder, strategy="sentence_window")
    result = search(
        "How often are production databases backed up?",
        index,
        embedder,
        top_k=3,
        expansion="sentence_window",
        window_size=1,
        max_context_chars=10_000,
    )
    assert any("every 6 hours" in r.text for r in result.results)
    blob = "\n".join(c.text for c in result.expanded_context)
    assert "every 6 hours" in blob
    assert result.budget["returned_chars"] <= result.budget["max_context_chars"]


def test_cli_build_search(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "sample.md").write_text(SAMPLE, encoding="utf-8")
    index = tmp_path / "index"
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "chunker.cli",
            "build",
            str(data),
            "--index",
            str(index),
            "--strategy",
            "parent-child",
            "--child-size",
            "16",
            "--parent-size",
            "128",
            "--overlap",
            "2",
            "--mock",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    search_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "chunker.cli",
            "search",
            "How often are production databases backed up?",
            "--index",
            str(index),
            "--mock",
            "--top-k",
            "5",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert search_proc.returncode == 0, search_proc.stderr
    payload = json.loads(search_proc.stdout)
    assert "results" in payload
    assert "expanded_context" in payload
