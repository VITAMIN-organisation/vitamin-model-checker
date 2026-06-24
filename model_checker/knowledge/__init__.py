import gzip
import json
from pathlib import Path
from typing import Any


def get_knowledge_documents() -> list[dict[str, Any]]:
    """Load documents from ``knowledge_bundle.json.gz``, or ``[]`` if missing."""
    bundle_path = Path(__file__).parent / "knowledge_bundle.json.gz"
    if not bundle_path.exists():
        return []

    try:
        with gzip.open(bundle_path, "rt", encoding="utf-8") as f:
            bundle = json.load(f)
            return bundle.get("documents", [])
    except Exception as e:
        import sys

        print(
            f"Warning: Failed to load VITAMIN knowledge bundle from {bundle_path}: {e}",
            file=sys.stderr,
        )
        return []


def get_bundle_metadata() -> dict[str, Any]:
    """Bundle version, git hash, and document count (or a status flag)."""
    bundle_path = Path(__file__).parent / "knowledge_bundle.json.gz"
    if not bundle_path.exists():
        return {"status": "missing"}

    try:
        with gzip.open(bundle_path, "rt", encoding="utf-8") as f:
            bundle = json.load(f)
            return {
                "status": "available",
                "version": bundle.get("version"),
                "git_hash": bundle.get("git_hash"),
                "total_documents": bundle.get("total_documents"),
            }
    except Exception:
        return {"status": "error"}
