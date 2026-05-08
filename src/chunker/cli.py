"""CLI: build, search, inspect, explain, evaluate, compare."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from chunker.config import ProjectConfig
from chunker.embedding.mock import MockEmbedder
from chunker.evaluation import compare_strategies, evaluate_index, load_benchmark
from chunker.pipeline import build_index, inspect_chunk, search


def _resolve_embedder(args: argparse.Namespace):
    if getattr(args, "mock", False):
        return MockEmbedder(dimension=getattr(args, "mock_dim", 32))
    from chunker.embedding.sentence_transformers import SentenceTransformerEmbedder

    model = getattr(args, "model", None) or "sentence-transformers/all-MiniLM-L6-v2"
    return SentenceTransformerEmbedder(model_name=model, normalize=True)


def _add_embedder_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Local sentence-transformers model name",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use deterministic MockEmbedder (no model download)",
    )
    parser.add_argument("--mock-dim", type=int, default=32, help="Mock embedder dimension")


def _normalize_strategy(value: str) -> str:
    mapping = {
        "parent-child": "parent_child",
        "parent_child": "parent_child",
        "direct": "direct",
        "sentence-window": "sentence_window",
        "sentence_window": "sentence_window",
    }
    key = value.strip().lower()
    if key not in mapping:
        raise ValueError(
            f"Unknown strategy {value!r}; expected parent-child, direct, or sentence-window"
        )
    return mapping[key]


def cmd_build(args: argparse.Namespace) -> int:
    embedder = _resolve_embedder(args)
    strategy = _normalize_strategy(args.strategy)
    summary = build_index(
        args.data,
        args.index,
        embedder,
        strategy=strategy,  # type: ignore[arg-type]
        child_size_tokens=args.child_size,
        parent_size_tokens=args.parent_size,
        overlap_tokens=args.overlap,
        config=ProjectConfig(),
    )
    print(json.dumps(summary, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    embedder = _resolve_embedder(args)
    expansion = None
    if args.expansion:
        expansion = args.expansion.replace("-", "_")
    result = search(
        args.query,
        args.index,
        embedder,
        top_k=args.top_k,
        expansion=expansion,  # type: ignore[arg-type]
        max_context_chars=args.max_context_chars,
        window_size=args.window_size,
        explain=False,
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    payload = inspect_chunk(args.index, args.chunk_id)
    print(json.dumps(payload, indent=2))
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    embedder = _resolve_embedder(args)
    expansion = None
    if args.expansion:
        expansion = args.expansion.replace("-", "_")
    result = search(
        args.query,
        args.index,
        embedder,
        top_k=args.top_k,
        expansion=expansion,  # type: ignore[arg-type]
        max_context_chars=args.max_context_chars,
        window_size=args.window_size,
        explain=True,
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    embedder = _resolve_embedder(args)
    expansion = args.expansion.replace("-", "_")
    benchmark = load_benchmark(Path(args.benchmark))
    report = evaluate_index(
        Path(args.index),
        benchmark,
        embedder,
        top_k=args.top_k,
        expansion=expansion,  # type: ignore[arg-type]
        window_size=args.window_size,
    )
    print(json.dumps({"metrics": report["metrics"], "top_k": report["top_k"]}, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    embedder = _resolve_embedder(args)
    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]
    report = compare_strategies(
        Path(args.data),
        Path(args.benchmark),
        Path(args.work_dir),
        embedder,
        strategies=strategies,
        top_k=args.top_k,
    )
    print(json.dumps(report, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chunker", description="Retrieval-aware chunker")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build local retrieval index")
    p_build.add_argument("data", type=Path, help="File or directory of .txt/.md sources")
    p_build.add_argument("--index", type=Path, default=Path("./index"))
    p_build.add_argument(
        "--strategy",
        default="parent-child",
        help="parent-child | direct | sentence-window",
    )
    p_build.add_argument("--child-size", type=int, default=256)
    p_build.add_argument("--parent-size", type=int, default=1024)
    p_build.add_argument("--overlap", type=int, default=32)
    _add_embedder_args(p_build)
    p_build.set_defaults(func=cmd_build)

    p_search = sub.add_parser("search", help="Retrieve top-K children and expand context")
    p_search.add_argument("query")
    p_search.add_argument("--index", type=Path, default=Path("./index"))
    p_search.add_argument("--top-k", type=int, default=5)
    p_search.add_argument(
        "--expansion",
        default=None,
        help="parent | sentence-window | none (default: index config)",
    )
    p_search.add_argument("--max-context-chars", type=int, default=None)
    p_search.add_argument("--window-size", type=int, default=2)
    _add_embedder_args(p_search)
    p_search.set_defaults(func=cmd_search)

    p_inspect = sub.add_parser("inspect", help="Inspect child/parent relationship")
    p_inspect.add_argument("chunk_id")
    p_inspect.add_argument("--index", type=Path, default=Path("./index"))
    p_inspect.set_defaults(func=cmd_inspect)

    p_explain = sub.add_parser("explain", help="Show retrieval/expansion stages")
    p_explain.add_argument("query")
    p_explain.add_argument("--index", type=Path, default=Path("./index"))
    p_explain.add_argument("--top-k", type=int, default=5)
    p_explain.add_argument("--expansion", default=None)
    p_explain.add_argument("--max-context-chars", type=int, default=None)
    p_explain.add_argument("--window-size", type=int, default=2)
    _add_embedder_args(p_explain)
    p_explain.set_defaults(func=cmd_explain)

    p_eval = sub.add_parser("evaluate", help="Run benchmark metrics on an index")
    p_eval.add_argument("benchmark", type=Path)
    p_eval.add_argument("--index", type=Path, default=Path("./index"))
    p_eval.add_argument("--top-k", type=int, default=5)
    p_eval.add_argument("--expansion", default="parent")
    p_eval.add_argument("--window-size", type=int, default=2)
    _add_embedder_args(p_eval)
    p_eval.set_defaults(func=cmd_evaluate)

    p_cmp = sub.add_parser("compare", help="Compare expansion strategies")
    p_cmp.add_argument("benchmark", type=Path)
    p_cmp.add_argument("--data", type=Path, default=Path("./data/corpus"))
    p_cmp.add_argument("--work-dir", type=Path, default=Path("./index/compare"))
    p_cmp.add_argument(
        "--strategies",
        default="direct,parent,sentence-window",
        help="Comma-separated strategy names",
    )
    p_cmp.add_argument("--top-k", type=int, default=5)
    _add_embedder_args(p_cmp)
    p_cmp.set_defaults(func=cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except (OSError, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    raise SystemExit(code)


if __name__ == "__main__":
    main()
