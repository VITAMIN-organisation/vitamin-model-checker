"""ICTL model checker state and formula tree construction."""

from typing import Any, Dict, Optional, Set

from model_checker.algorithms.explicit.ICTL.util.graph import (
    get_preorder,
    labeled_pairs,
)
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.utils.formula_tree import FormulaTreeNode, build_formula_tree


def states_where_prop_holds(prop: str, prop_matrix, propositions) -> Optional[Set[int]]:
    """Return state indices where prop holds, or None if the atom is unknown."""
    index = proposition_index(propositions, prop)
    if index is None:
        return None
    return {
        state_idx for state_idx, row in enumerate(prop_matrix) if row[int(index)] == 1
    }


class ICTLModelChecker:
    """ICTL checker over a birelational model dict loaded from graph I/O."""

    def __init__(self, model: Dict[str, Any]) -> None:
        self.data = model
        graph = self.data["graph"]
        states = self.data["states"]
        self.edges = labeled_pairs(graph, states, lambda cell: cell not in ("0", "P"))
        self.preorder_edges = labeled_pairs(
            graph, states, lambda cell: cell in ("P,R", "P")
        )
        self.upward_closure = get_preorder(self.preorder_edges, states)

    @property
    def states_set(self) -> Set[str]:
        return {str(s) for s in self.data["states"]}

    def states_with_upset_in(self, target: Set[str]) -> Set[str]:
        """States whose P-upset is contained in target (paper ^up operator)."""
        closures = self.upward_closure
        return {state for state in self.states_set if closures[state].issubset(target)}

    def build_tree(self, parsed_formula) -> Optional[FormulaTreeNode]:
        """Build a formula tree with atoms resolved to state sets."""

        def resolve_atom(atom) -> Optional[str]:
            indices = states_where_prop_holds(
                str(atom), self.data["matrix_prop"], self.data["atomic_propositions"]
            )
            if indices is None:
                return None
            states = {str(self.data["states"][idx]) for idx in indices}
            return str(states)

        return build_formula_tree(parsed_formula, resolve_atom)
