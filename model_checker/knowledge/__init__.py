import gzip
import json
from pathlib import Path
from typing import Any, Dict, List


def get_knowledge_documents() -> List[Dict[str, Any]]:
    """
    Load the pre-compiled knowledge documents from the bundle.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries with 'content' and 'metadata'.
        Returns an empty list if the bundle doesn't exist or is corrupted.
    """
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


def get_bundle_metadata() -> Dict[str, Any]:
    """
    Retrieve metadata about the current knowledge bundle.

    Returns:
        Dict[str, Any]: Metadata including version, git_hash, and document count.
    """
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
