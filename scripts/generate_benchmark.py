#!/usr/bin/env python3
"""Generate PRD-scale technical corpus and gold retrieval benchmark."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "corpus"
BENCH = ROOT / "benchmarks" / "retrieval.json"
SAMPLE = ROOT / "data" / "sample.md"

TOPICS = [
    ("backups", "Backup Policy", "every 6 hours", "Backups are performed every 6 hours."),
    ("retention", "Retention Rules", "30 days", "Backup retention is 30 days."),
    ("restore", "Restore Process", "require approval", "Restore requests require approval."),
    ("replication", "Replication", "cross-region", "Replicas are kept in a cross-region pair."),
    ("encryption", "Encryption", "AES-256", "Data at rest uses AES-256 encryption."),
    ("auth", "Authentication", "SSO only", "Interactive logins are SSO only."),
    ("rate_limit", "Rate Limits", "100 requests per minute", "API clients are limited to 100 requests per minute."),
    ("timeouts", "Timeouts", "30 seconds", "Upstream timeouts are set to 30 seconds."),
    ("caching", "Caching", "5 minute TTL", "Responses are cached with a 5 minute TTL."),
    ("logging", "Logging", "JSON lines", "Application logs are emitted as JSON lines."),
    ("metrics", "Metrics", "Prometheus", "Service metrics are scraped by Prometheus."),
    ("alerts", "Alerting", "PagerDuty", "Critical pages route to PagerDuty."),
    ("deploy", "Deployments", "blue-green", "Production releases use blue-green deployments."),
    ("rollback", "Rollback", "previous revision", "Failed releases roll back to the previous revision."),
    ("secrets", "Secrets", "vault-backed", "Secrets are vault-backed and rotated weekly."),
    ("network", "Networking", "private VPC", "Services run inside a private VPC."),
    ("cdn", "CDN", "edge cache", "Static assets are served from an edge cache."),
    ("queue", "Queues", "at-least-once", "Workers consume messages with at-least-once delivery."),
    ("schema", "Schema Changes", "expand-contract", "Migrations follow the expand-contract pattern."),
    ("sla", "SLA", "99.9 percent", "The availability target is 99.9 percent."),
]


def doc_text(topic_key: str, title: str, fact: str, idx: int) -> str:
    return f"""# {title} (variant {idx})

## Overview
This document describes the {title.lower()} used by service cluster {idx}.

## Policy
{fact}
Related configuration keys are namespaced under `{topic_key}.v{idx}`.

## Operations
Operators should verify the {title.lower()} after each change window.
Escalation contacts are listed in the on-call roster for cluster {idx}.

## Notes
Do not confuse this policy with legacy settings from cluster {idx - 1 if idx else 0}.
"""


def main() -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    BENCH.parent.mkdir(parents=True, exist_ok=True)

    SAMPLE.write_text(
        """# Database Backups
Production databases are backed up every 6 hours.
Backups are retained for 30 days.
Restore requests require approval.
""",
        encoding="utf-8",
    )

    queries: list[dict] = []
    doc_count = 0

    # 5 variants per topic => 100 docs
    for t_idx, (key, title, phrase, fact) in enumerate(TOPICS):
        for v in range(5):
            doc_id = f"{key}_{v:02d}"
            path = CORPUS / f"{doc_id}.md"
            path.write_text(doc_text(key, title, fact, v), encoding="utf-8")
            doc_count += 1

            # One query per document (100 queries) — take first 60 for PRD floor+
            if len(queries) < 60:
                queries.append(
                    {
                        "query_id": f"q_{doc_id}",
                        "query": f"What is the {title.lower()} for cluster {v}?",
                        "document_id": doc_id,
                        "gold_child_contains": [phrase],
                        "gold_context_contains": [phrase, title],
                        "metadata": {"topic": key, "variant": v},
                    }
                )

    # Extra fact-focused queries for sample-like phrasing on first variants
    extras = [
        ("backups_00", "How often are backups performed?", "every 6 hours"),
        ("retention_00", "How long are backups retained?", "30 days"),
        ("restore_00", "Do restore requests need approval?", "require approval"),
        ("encryption_00", "What encryption is used at rest?", "AES-256"),
        ("rate_limit_00", "What is the API rate limit?", "100 requests per minute"),
    ]
    for doc_id, query, phrase in extras:
        queries.append(
            {
                "query_id": f"q_extra_{doc_id}",
                "query": query,
                "document_id": doc_id,
                "gold_child_contains": [phrase],
                "gold_context_contains": [phrase],
            }
        )

    BENCH.write_text(
        json.dumps({"version": 1, "queries": queries}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {doc_count} docs to {CORPUS}")
    print(f"Wrote {len(queries)} queries to {BENCH}")


if __name__ == "__main__":
    main()
