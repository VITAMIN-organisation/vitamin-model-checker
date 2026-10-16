"""Compatibility API for strict Recall CGS preflight validation."""
from model_checker.parsers.game_structures.cgs.semantic_snapshot import prepare_cgs


def validate_recall_cgs_semantics(cgs):
    """Return the validated transition map, without mutating the input model."""
    return {s: dict(row) for s, row in prepare_cgs(cgs).transitions.items()}
