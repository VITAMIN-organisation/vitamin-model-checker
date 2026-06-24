"""Resolve atomic propositions to sets of states."""

from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from model_checker.parsers.game_structures.cgs import CGSProtocol
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.utils.formula_tree import build_formula_tree


@runtime_checkable
class AtomicModel(Protocol):
    """Model with atomic proposition names and a state labelling matrix."""

    atomic_propositions: Any
    matrix_prop: Any


def states_where_prop_holds(cgs: CGSProtocol, prop: str) -> set[str] | None:
    """Return states where prop holds, or None if the proposition is unknown."""
    idx = proposition_index(cgs.atomic_propositions, prop)
    if idx is None:
        return None

    matching: set[str] = set()
    prop_matrix = cgs.matrix_prop
    for state_idx, row in enumerate(prop_matrix):
        if row[int(idx)] == 1:
            matching.add(str(cgs.get_state_name_by_index(state_idx)))
    return matching


def resolve_atom(cgs: AtomicModel, atom: str) -> set[str] | None:
    """Return the states where ``atom`` is true, or None if the atom is not in the model."""
    states = states_where_prop_holds(cgs, str(atom))
    if states is None:
        return None
    return {str(s) for s in states}


def resolve_atom_with_constants(
    cgs: AtomicModel, atom: str, parser: Any
) -> set[str] | None:
    """Resolve an atom, treating TRUE as all states and FALSE as none."""
    s = str(atom)
    if parser.verify("FALSE", s):
        return set()
    if parser.verify("TRUE", s):
        all_states = cgs.all_states_set
        return set(all_states) if not isinstance(all_states, set) else all_states

    return resolve_atom(cgs, s)


def build_resolved_formula_tree(
    cgs: AtomicModel,
    tpl: Any,
    parser: Any = None,
    atom_resolver: Callable[[Any], Any] | None = None,
) -> Any:
    """Build a formula tree with leaf atoms resolved from the model."""
    if atom_resolver is not None:
        return build_formula_tree(tpl, atom_resolver)
    if parser is not None:

        def resolve_with_constants(atom: Any) -> set[str] | None:
            return resolve_atom_with_constants(cgs, atom, parser)

        return build_formula_tree(tpl, resolve_with_constants)

    def resolve_proposition(atom: Any) -> set[str] | None:
        return resolve_atom(cgs, str(atom))

    return build_formula_tree(tpl, resolve_proposition)
