"""Public VITAMIN entry point for NatATL with natural recall strategies.

Uses the compositional NatATL AST evaluator and the automata-product Recall
backend. In particular, this entry point does not lower nested strategic
modalities to one global CTL formula or unfold the CGS to a fixed depth.

For the supported Boolean/regular guard grammar, completed extended
bounded enumeration provides two-valued results. Other guard grammars
require separate completeness arguments; this API does not claim them.
"""

from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.recall_compositional import (
    check_compositional_recall,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.game_structures.cgs.cgs import CGS


def _core_natatl_recall_checking(cgs: CGS, formula: str) -> dict[str, Any]:
    """Verify NatATL Recall using exact finite products, not bounded trees.

    A strict deterministic/total CGS preflight precedes formula evaluation.
    Each nested strategic modality is checked with its own strategy search.
    """
    return check_compositional_recall(
        cgs, formula, generator="extended", complete_supported_grammar=True
    )


model_checking = create_model_checking_entry("NatATL", _core_natatl_recall_checking)
