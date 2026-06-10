"""Resolve atomic propositions to sets of states."""

from typing import Any, Callable, Optional, Protocol, Set, runtime_checkable

from model_checker.engine.runner import build_formula_tree, states_where_prop_holds


@runtime_checkable
class AtomicModel(Protocol):
    """Model with atomic proposition names and a state labelling matrix."""

    atomic_propositions: Any
    matrix_prop: Any


def resolve_atom(cgs: AtomicModel, atom: str) -> Optional[Set[str]]:
    """Return the states where ``atom`` is true, or None if the atom is not in the model."""
    states = states_where_prop_holds(cgs, str(atom))
    if states is None:
        return None
    return {str(s) for s in states}


def resolve_atom_with_constants(
    cgs: AtomicModel, atom: str, parser: Any
) -> Optional[Set[str]]:
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
    atom_resolver: Optional[Callable[[Any], Any]] = None,
) -> Any:
    """Build a formula tree with leaf atoms resolved from the model."""
    if atom_resolver is not None:
        return build_formula_tree(tpl, atom_resolver)
    if parser is not None:

        def resolve_with_constants(atom: Any) -> Optional[Set[str]]:
            return resolve_atom_with_constants(cgs, atom, parser)

        return build_formula_tree(tpl, resolve_with_constants)

    def resolve_proposition(atom: Any) -> Optional[Set[str]]:
        return resolve_atom(cgs, str(atom))

    return build_formula_tree(tpl, resolve_proposition)
