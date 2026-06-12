"""IATL model checker state and formula tree construction."""

from typing import Any, Dict, Optional, Set

import numpy as np

from model_checker.algorithms.explicit.IATL.preimage import (
    TransitionCache,
    build_transition_cache,
)
from model_checker.algorithms.explicit.ICTL.util.graph import (
    get_preorder,
    labeled_pairs,
)
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.utils.formula_tree import FormulaTreeNode, build_formula_tree


class IATLModelChecker:
    """IATL checker over a BCGS model dict loaded from file I/O."""

    def __init__(self, model: Dict[str, Any]) -> None:
        self.data = model
        self._transition_caches: Dict[str, TransitionCache] = {}
        states = self.data["states"]
        preorder_edges = labeled_pairs(
            self.data["preorder"], states, lambda cell: cell == 1
        )
        self.upward_closure = get_preorder(preorder_edges, states)

    @property
    def states_set(self) -> Set[str]:
        return {str(state) for state in self.data["states"]}

    def transition_cache_for(self, coalition: str) -> TransitionCache:
        """Return cached coalition-grouped transitions, building on first use."""
        cache = self._transition_caches.get(coalition)
        if cache is None:
            cache = build_transition_cache(
                self.data["graph"],
                self.data["number_of_agents"],
                coalition,
            )
            self._transition_caches[coalition] = cache
        return cache

    def build_tree(self, parsed_formula) -> Optional[FormulaTreeNode]:
        """Build a formula tree with atoms resolved to state sets."""

        def resolve_atom(atom) -> Optional[str]:
            prop_idx = proposition_index(self.data["atomic_propositions"], str(atom))
            if prop_idx is None:
                return None
            state_indices = set(
                np.where(self.data["matrix_prop"][:, int(prop_idx)] == 1)[0]
            )
            states = self.data["states"]
            return str({str(states[idx]) for idx in state_indices})

        return build_formula_tree(parsed_formula, resolve_atom)
