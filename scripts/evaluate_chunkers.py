"""
scripts/evaluate_chunkers.py — Isolated per-chunker retrieval benchmark for PKA-AI.

Usage:
    python -m scripts.evaluate_chunkers --chunker v1 --out data/evaluation/eval_results_v1.json
    python -m scripts.evaluate_chunkers --chunker v2 --out data/evaluation/eval_results_v2.json

Runs the same methodology as scripts/evaluate_retrieval.py, but against a
fresh, temporary ChromaDB store built with exactly one chunker:

    1. Load every supported document from data/raw/ (load_folder).
    2. Chunk with the requested chunker, embed with EmbeddingClient,
       store with store_chunks() into a temporary store.
    3. Run data/evaluation/eval_queries.json through semantic_search_reranked().
    4. Score with the unchanged correct_at_1() / hit_in_topk() metrics.
    5. Write results to --out, then delete the temporary store.

Isolation
---------
src.retrieval.search and src.vectorstore.chroma_store each construct a
module-level ChromaClient() at import time, which opens CHROMA_DB_PATH
(./chroma_db). To guarantee the original store is never opened, the
CHROMA_DB_PATH config value is redirected to the temporary directory
*before* those modules are imported, and the evaluation client is also
injected explicitly into store_chunks() and semantic_search_reranked().
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

RAW_DATA_PATH = "./data/raw"
CHUNKERS      = ("v1", "v2")
# Same as evaluate_retrieval.RESULTS_PATH; not imported from there because that
# import opens ./chroma_db (see "Isolation" above).
BASELINE_RESULTS_PATH = Path("data/evaluation/eval_results.json")


# ── Metadata helpers ──────────────────────────────────────────────────────────

def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"  ⚠️  Could not read git commit: {e}", file=sys.stderr)
        return None


def _model_digest(model_name: str) -> str | None:
    import ollama

    wanted = model_name if ":" in model_name else f"{model_name}:latest"
    try:
        for model in ollama.list().models:
            if model.model == wanted:
                return model.digest
    except Exception as e:
        print(f"  ⚠️  Could not read embedding model digest: {e}", file=sys.stderr)
        return None
    print(f"  ⚠️  Embedding model {wanted} not found in `ollama list`", file=sys.stderr)
    return None


# ── Runner ────────────────────────────────────────────────────────────────────

def run(chunker_name: str, out_path: Path, db_dir: Path) -> None:
    # Redirect the default store BEFORE importing anything that builds a
    # module-level ChromaClient — see "Isolation" in the module docstring.
    import src.config.config as config
    config.CHROMA_DB_PATH = str(db_dir)

    # Imported first so its logging.basicConfig(WARNING) wins over the
    # loader's basicConfig(INFO), keeping output as quiet as evaluate_retrieval.
    from scripts.evaluate_retrieval import (
        QUERIES_PATH, TOP_K, correct_at_1, hit_in_topk, source_of, _print_report,
    )
    from src.core.chroma_client import ChromaClient
    from src.core.embedding_client import EmbeddingClient
    from src.ingestion.chunking import ChunkerV1, ChunkerV2
    from src.ingestion.loader import load_folder
    from src.retrieval.search import semantic_search_reranked
    from src.vectorstore.chroma_store import store_chunks

    chunker = {"v1": ChunkerV1, "v2": ChunkerV2}[chunker_name]()
    embed_client = EmbeddingClient()
    chroma = ChromaClient(db_path=str(db_dir), collection_name=f"eval_{chunker.version}")
    try:
        collection = chroma.get_collection()

        if collection.count() != 0:
            raise RuntimeError(f"Evaluation store {db_dir} is not empty")

        with open(QUERIES_PATH, encoding="utf-8") as f:
            queries = json.load(f)

        # ── Ingest ──
        print(f"\n🔄 Ingesting {RAW_DATA_PATH} with Chunker{chunker.version.upper()} → {db_dir}")
        docs = load_folder(RAW_DATA_PATH)
        if not docs:
            raise RuntimeError(f"No documents found in {RAW_DATA_PATH}")

        total_chunks = 0
        for doc in docs:
            chunks = chunker.chunk_document(doc["content"], source=doc["path"])
            vectors = [embed_client.generate(chunk["text"]) for chunk in chunks]
            store_chunks(chunks=chunks, embeddings=vectors, chroma_client=chroma)
            total_chunks += len(chunks)
            print(f"  {doc['path']}: {len(chunks)} chunks")

        # Every stored chunk must come from this run's chunker — never mixed.
        stored = collection.get(include=["metadatas"])["metadatas"]
        versions = Counter(m.get("chunker_version") for m in stored)
        if len(stored) != total_chunks or set(versions) != {chunker.version}:
            raise RuntimeError(
                f"Store integrity check failed: expected {total_chunks} "
                f"'{chunker.version}' chunks, found {dict(versions)}"
            )

        # ── Evaluate ──
        print(f"\n🔍 Evaluating {len(queries)} queries (top_k={TOP_K}) …\n")
        results = []
        for item in queries:
            expected = item["expected_source"]
            chunks = semantic_search_reranked(
                item["query"], top_k=TOP_K,
                embedding_client=embed_client, chroma_client=chroma,
            )

            at1  = correct_at_1(chunks, expected)
            in_k = hit_in_topk(chunks, expected)
            top1 = source_of(chunks[0]) if chunks else "—"
            dist = chunks[0].get("distance") if chunks else None

            status = "✅" if at1 else ("⚠️ " if in_k else "❌")
            print(f"  {status} [{item['id']}] {item['query']}")

            results.append({
                "id":              item["id"],
                "query":           item["query"],
                "expected_source": expected,
                "actual_top1":     top1,
                "correct_at_1":    at1,
                "hit_in_topk":     in_k,
                "top1_distance":   round(dist, 4) if dist is not None else None,
                "notes":           item.get("notes", ""),
                "retrieved": [
                    {
                        "rank":        rank,
                        "source":      source_of(c),
                        "chunk_index": c["metadata"].get("chunk_index"),
                        "distance":    round(c["distance"], 4),
                        "final_score": round(c["rerank_scores"]["final_score"], 4),
                    }
                    for rank, c in enumerate(chunks, start=1)
                ],
            })

        _print_report(results, len(results))

        # Summary counts use the same definitions as evaluate_retrieval._print_report().
        at1_count  = sum(1 for r in results if r["correct_at_1"])
        hitk_count = sum(1 for r in results if r["hit_in_topk"])
        payload = {
            "date":            str(date.today()),
            "top_k":           TOP_K,
            "chunker_version": chunker.version,
            "git_commit":      _git_commit(),
            "embedding_model": embed_client.model_name,
            "embedding_model_digest": _model_digest(embed_client.model_name),
            "timestamp":       datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "num_documents":   len(docs),
            "num_chunks":      total_chunks,
            "num_queries":     len(results),
            "accuracy_at_1":   at1_count / len(results),
            "hit_rate_at_k":   hitk_count / len(results),
            "correct_at_1_count": at1_count,
            "hit_in_topk_count":  hitk_count,
            "wrong_rank_count":   sum(1 for r in results if r["hit_in_topk"] and not r["correct_at_1"]),
            "complete_miss_count": sum(1 for r in results if not r["hit_in_topk"]),
            "results":         results,
        }

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"\n  Results saved → {out_path}\n")

    finally:
        # Release ChromaDB's file handles so the temporary store can be
        # deleted (Windows refuses to remove open files).
        chroma._client._system.stop()
        chroma._client.clear_system_cache()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--chunker", required=True, choices=CHUNKERS)
    parser.add_argument("--out", required=True, type=Path, help="Output JSON path")
    args = parser.parse_args()

    if args.out.resolve() == BASELINE_RESULTS_PATH.resolve():
        parser.error(f"--out must not overwrite the baseline file {BASELINE_RESULTS_PATH}")

    db_dir = Path(tempfile.mkdtemp(prefix=f"pka_eval_{args.chunker}_"))
    try:
        run(args.chunker, args.out, db_dir)
    finally:
        shutil.rmtree(db_dir)
        print(f"  🧹 Removed temporary store {db_dir}")


if __name__ == "__main__":
    main()
