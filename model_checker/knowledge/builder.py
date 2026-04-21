import os
import json
import gzip
import subprocess
from pathlib import Path

def get_git_hash(repo_root):
    """Attempt to get the current git commit hash."""
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], 
            cwd=repo_root, 
            stderr=subprocess.DEVNULL
        ).decode('ascii').strip()
    except Exception:
        return None

def build_knowledge():
    """Scan the repository and build a compressed knowledge bundle."""
    # Root of the vitamin-model-checker repo
    root = Path(__file__).resolve().parents[2]
    knowledge_dir = root / "model_checker" / "knowledge"
    output_file = knowledge_dir / "knowledge_bundle.json.gz"
    
    print(f"Building knowledge bundle for: {root}")
    
    documents = []
    
    # 1. Load README.md
    readme = root / "README.md"
    if readme.exists():
        documents.append({
            "content": readme.read_text(errors='ignore'),
            "metadata": {"source": "README.md", "type": "documentation"}
        })

    # 2. Load docs/ directory
    docs_dir = root / "docs"
    if docs_dir.exists():
        for md_file in docs_dir.rglob("*.md"):
            documents.append({
                "content": md_file.read_text(errors='ignore'),
                "metadata": {
                    "source": str(md_file.relative_to(root)), 
                    "type": "documentation"
                }
            })

    # 3. Load model_checker/ directory (Python files)
    pkg_dir = root / "model_checker"
    for py_file in pkg_dir.rglob("*.py"):
        # Skip internal/cache/test files to keep bundle size reasonable
        rel_path = py_file.relative_to(root)
        if any(part in py_file.parts for part in ["__pycache__", "tests", ".pytest_cache"]):
            continue
        
        # Also skip generated parser files (usually too large and noisy for LLMs)
        if py_file.name in ["parsetab.py", "parser.out"]:
            continue
            
        documents.append({
            "content": py_file.read_text(errors='ignore'),
            "metadata": {
                "source": str(rel_path), 
                "type": "code"
            }
        })

    bundle = {
        "version": "1.0",
        "git_hash": get_git_hash(root),
        "total_documents": len(documents),
        "documents": documents
    }

    # Write compressed JSON
    with gzip.open(output_file, 'wt', encoding='utf-8') as f:
        json.dump(bundle, f)
    
    print(f"Successfully created: {output_file}")
    print(f"Total documents indexed: {len(documents)}")

if __name__ == "__main__":
    build_knowledge()
