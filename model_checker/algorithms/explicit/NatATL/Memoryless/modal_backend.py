
"""Compositional NatATL memoryless backend with state-set semantics."""

from collections.abc import Callable

from model_checker.algorithms.explicit.NatATL.Memoryless.lazy_generation import (
    collective_strategies,
)
from model_checker.algorithms.explicit.NatATL.strategy_complexity import (
    individual_complexity,
)


def universal_temporal_states(
    successors: dict[str, set[str]],
    op: str,
    left: set[str],
    right: set[str] | None = None,
) -> set[str]:
    """Evaluate universal temporal operators over a finite total graph."""

    states = set(successors)

    if not states or any(
        not targets or not targets <= states
        for targets in successors.values()
    ):
        raise ValueError(
            "Temporal evaluation requires a total transition relation"
        )

    if not left <= states or (
        right is not None and not right <= states
    ):
        raise ValueError("Temporal operand references unknown states")

    def ax(target: set[str]) -> set[str]:
        return {
            state
            for state, targets in successors.items()
            if targets <= target
        }

    if op == "X":
        if right is not None:
            raise ValueError("X expects one operand")
        return ax(left)

    if op not in {"F", "G", "U", "W"}:
        raise ValueError(f"Unsupported temporal operator: {op}")

    if (op in {"U", "W"}) != (right is not None):
        raise ValueError(f"Incorrect operands for {op}")

    if op == "F":
        target, invariant, least = left, states, True
    elif op == "G":
        target, invariant, least = set(), left, False
    else:
        assert right is not None  # Required for U and W.
        target, invariant, least = right, left, op == "U"

    # F and U use least fixpoints.
    # G and W use greatest fixpoints.
    current = set() if least else set(states)

    while True:
        updated = target | (invariant & ax(current))

        if updated == current:
            return updated

        current = updated


def make_modal_backend(cgs, model_path: str, *, appropriateness="first-match") -> Callable:
    """Build one run-local evaluator; full state-set results are the default.

    ``needed`` is only for callers explicitly requesting a partial decision.
    Never pass the initial state as ``needed`` for nested state-set operands.
    """
    from model_checker.algorithms.explicit.NatATL.Memoryless.pruning import (
        compile_memoryless_profile,
    )
    from model_checker.algorithms.explicit.NatATL.strategy_errors import (
        InadmissibleStrategy,
    )
    from model_checker.parsers.game_structures.cgs.semantic_snapshot import prepare_cgs
    snapshot = prepare_cgs(cgs)
    names = snapshot.states
    states = set(names)
    guard_cache = {}

    def backend(agents, k, op, left, right, *, needed=None):
        if type(k) is not int or k < 0 or len(set(agents)) != len(agents):
            raise ValueError("Invalid coalition or complexity bound")
        if any(type(a) is not int or a < 1 or a > snapshot.number_of_agents for a in agents):
            raise ValueError("Invalid coalition agent")
        required_states = states if needed is None else set(needed)
        if not required_states <= states:
            raise ValueError("Unknown requested state")
        actions_by_agent = {a: sorted(set().union(*(snapshot.enabled[s][a] for s in names)))
                            for a in agents}
        winners = set()
        backend.witnesses = {}
        backend.stats = {"Candidates Examined": 0, "Duplicate Policies Skipped": 0,
                         "Temporal Checks": 0}
        seen = set()
        for candidate in collective_strategies(
            agents=agents, actions_by_agent=actions_by_agent,
            propositions=snapshot.propositions, bound=k,
        ):
            backend.stats["Candidates Examined"] += 1
            try:
                selected = compile_memoryless_profile(
                    snapshot, agents, candidate, appropriateness=appropriateness,
                    guard_cache=guard_cache,
                )
            except InadmissibleStrategy:
                continue
            signature = tuple(selected[state] for state in names)
            if signature in seen:
                backend.stats["Duplicate Policies Skipped"] += 1
                continue
            seen.add(signature)
            successors = {s: {t for t, joint in snapshot.outgoing[s]
                              if all(joint[a-1] == action for a, action in zip(agents, selected[s], strict=True))}
                          for s in names}
            backend.stats["Temporal Checks"] += 1
            winning_states = universal_temporal_states(successors, op, left, right)
            for state in winning_states - winners:
                backend.witnesses[state] = candidate
            winners.update(winning_states)
            if required_states <= winners:
                break
        return winners
    backend.witnesses = {}
    backend.stats = {}
    return backend



def check_memoryless_formula(
    formula: str,
    model_path: str,
    *, appropriateness="first-match", return_all_states=True,
) -> dict:
    """Compositional NatATL memoryless verification."""

    from model_checker.algorithms.explicit.NatATL.compositional import (
        MODAL,
        satisfying_states,
    )
    from model_checker.algorithms.explicit.NatATL.natatl_ast import (
        parse_natatl_formula,
    )
    from model_checker.algorithms.explicit.shared.atom_utils import (
        states_where_prop_holds,
    )
    from model_checker.parsers.game_structures.cgs import CGS

    cgs = CGS()
    cgs.read_file(model_path)

    ast = parse_natatl_formula(
        formula,
        cgs.get_number_of_agents(),
    )

    universe = {str(state) for state in cgs.states}

    valuation: dict[str, set[str]] = {}
    for prop in cgs.atomic_propositions:
        atom = str(prop)
        matching_states = states_where_prop_holds(cgs, atom)
        if matching_states is None:
            raise ValueError(f"Undefined valuation for declared atom: {atom}")
        valuation[atom] = matching_states

    def validate_atoms(node):
        if isinstance(node, str):
            if node.lower() not in ("true", "false") and node not in ("T",) and node not in valuation:
                raise ValueError(f"Unknown atomic proposition: {node}")
        elif isinstance(node, tuple):
            for child in node[1:]:
                validate_atoms(child)
    validate_atoms(ast)
    modal_backend = make_modal_backend(cgs, model_path, appropriateness=appropriateness)

    root_modal = (isinstance(ast, tuple) and isinstance(ast[0], str)
                  and MODAL.fullmatch(ast[0]))
    if not return_all_states and root_modal:
        # Decide children exactly in the ORIGINAL CGS, then stop only the root search.
        left = satisfying_states(ast[1], universe, valuation, modal_backend)
        right = (satisfying_states(ast[2], universe, valuation, modal_backend)
                 if len(ast) == 3 else None)
        aliases = {"NEXT": "X", "EVENTUALLY": "F", "GLOBALLY": "G", "ALWAYS": "G",
                   "UNTIL": "U", "WEAKUNTIL": "W"}
        op = root_modal.group("op").upper()
        result_states = modal_backend(
            tuple(int(a) for a in root_modal.group("agents").split(",") if a),
            int(root_modal.group("bound")), aliases.get(op, op), left, right,
            needed={str(cgs.initial_state)},
        ) & {str(cgs.initial_state)}
    else:
        result_states = satisfying_states(ast, universe, valuation, modal_backend)

    initial = str(cgs.initial_state)
    satisfied = initial in result_states

    result = {
        "Satisfiability": satisfied,
        "Satisfying States": sorted(result_states),
        "res": "Result: " + ("{" + ", ".join(repr(s) for s in sorted(result_states)) + "}" if result_states else "set()"),
        "Appropriateness": appropriateness,
        "State Set Complete": bool(return_all_states or not root_modal),
        "initial_state": (
            f"Initial state {initial}: {satisfied}"
        ),
    }

    # A top-level strategic modality has a witness
    # for its existential strategy quantifier.
    if (
        isinstance(ast, tuple)
        and ast
        and isinstance(ast[0], str)
        and (match := MODAL.fullmatch(ast[0]))
    ):
        bound = int(match.group("bound"))

        result["Complexity Bound"] = bound
        result["Requested Complexity Bound"] = bound

        if satisfied:
            witness = modal_backend.witnesses.get(initial)

            if witness is None:
                raise AssertionError(
                    "Missing witness for satisfied modality"
                )

            cost = sum(
                individual_complexity(
                    strategy["condition_action_pairs"]
                )
                for strategy in witness
            )

            if cost > bound:
                raise AssertionError(
                    "Witness exceeds complexity bound"
                )

            result["Winning Strategy per agent"] = witness
            result["Witness Complexity"] = cost


    if not result["State Set Complete"]:
        result["Queried States"] = [initial]
        result["Satisfying Queried States"] = result.pop("Satisfying States")
    result["Search Statistics"] = dict(modal_backend.stats)
    return result
