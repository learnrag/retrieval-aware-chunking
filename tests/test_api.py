"""API smoke tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from chunker.api import app

client = TestClient(app)

SAMPLE = """# Database Backups
Production databases are backed up every 6 hours.
Backups are retained for 30 days.
Restore requests require approval.
"""


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_build_search_inspect(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "sample.md").write_text(SAMPLE, encoding="utf-8")
    index = tmp_path / "index"

    build = client.post(
        "/build",
        json={
            "data_path": str(data),
            "index_path": str(index),
            "strategy": "parent_child",
            "child_size_tokens": 16,
            "parent_size_tokens": 128,
            "overlap_tokens": 2,
            "mock": True,
        },
    )
    assert build.status_code == 200, build.text
    assert build.json()["children"] >= 1

    search = client.post(
        "/search",
        json={
            "query": "How often are production databases backed up?",
            "index_path": str(index),
            "top_k": 5,
            "mock": True,
        },
    )
    assert search.status_code == 200, search.text
    body = search.json()
    assert body["results"]
    child_id = body["results"][0]["child_id"]

    inspect = client.post(
        "/inspect",
        json={"chunk_id": child_id, "index_path": str(index)},
    )
    assert inspect.status_code == 200
    assert inspect.json()["child"]["chunk_id"] == child_id
