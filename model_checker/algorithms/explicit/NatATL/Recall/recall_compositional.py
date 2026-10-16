"""Compositional NatATL Recall model checking over finite CGSs.

The extended generator enumerates the entire supported bounded regular-guard
grammar and is complete *within that grammar*. Explicit certification turns
its exhausted searches into definitive negatives, including inside negation
and nested modalities. The older canonical generator remains conservative.
No statement is made about alternative/unsupported NatATL guard syntax.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from typing import Any

from model_checker.algorithms.explicit.NatATL.Recall.recall_appropriateness import (
    InappropriateRecallRule,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_product import (
    build_validated_recall_product,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_solver import (
    solve_bounded_recall,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_temporal import (
    check_initial,
)

_MODAL = re.compile(r"^<\{(?P<agents>\d+(?:,\d+)*)\},\s*(?P<bound>\d+)>(?P<op>[A-Za-z]+)$")
_OPS = {
    "X": "X", "NEXT": "X", "F": "F", "EVENTUALLY": "F",
    "G": "G", "GLOBALLY": "G", "ALWAYS": "G",
    "U": "U", "UNTIL": "U", "W": "W", "WEAKUNTIL": "W",
}
_NOT = frozenset({"!", "NOT"})
_AND = frozenset({"&&", "&", "AND"})
_OR = frozenset({"||", "|", "OR"})
_IMP = frozenset({"->", ">", "IMPLIES"})


@dataclass(frozen=True)
class Evidence:
    """Sets with proven true/false status; all other states are UNKNOWN."""

    true: frozenset[str]
    false: frozenset[str]


def check_compositional_recall_ast(
    cgs: Any,
    ast: Any,
    *,
    initial_state: str | None = None,
    generator: str = "canonical",
    complete_supported_grammar: bool = False,
) -> dict[str, Any]:
    """Evaluate NatATL Recall recursively on every CGS state.

    No bounded unfolding or global strategy reuse across nested modalities.
    Negative verdicts require separate, auditable certificates.
    ``complete_supported_grammar`` requires the extended structural generator;
    it must not be enabled for the incomplete canonical strategy fragment.
    """
    if generator not in ("canonical", "extended") or not isinstance(generator, str):
        raise ValueError("generator must be 'canonical' or 'extended'")
    if type(complete_supported_grammar) is not bool:
        raise ValueError("complete_supported_grammar must be a Boolean")
    if complete_supported_grammar and generator != "extended":
        raise ValueError("Complete supported-grammar checking requires generator='extended'")
    from model_checker.algorithms.explicit.NatATL.Recall.recall_context import (
        RecallContext,
    )
    context = RecallContext(cgs)
    view = context.snapshot
    states, propositions, n_agents = view.states, view.propositions, view.number_of_agents
    labels, successors = view.labels, view.successors
    universe = frozenset(states)
    start = str(cgs.initial_state if initial_state is None else initial_state)
    if start not in universe:
        raise ValueError(f"Unknown initial state {start!r}")

    atomic_props = set(propositions)
    cache: dict[Any, Evidence] = {}
    witnesses: dict[tuple[Any, str], dict[str, Any]] = {}
    refutations: dict[tuple[Any, str], tuple[int, str]] = {}
    reachable_cache: dict[str, frozenset[str]] = {}

    def reachable(start_state: str) -> frozenset[str]:
        """All states reachable in the UNPRUNED CGS, including the start."""
        if start_state not in reachable_cache:
            found = {start_state}
            queue = deque([start_state])
            while queue:
                for successor in successors[queue.popleft()]:
                    if successor not in found:
                        found.add(successor)
                        queue.append(successor)
            reachable_cache[start_state] = frozenset(found)
        return reachable_cache[start_state]

    def minimal_profile_loses(
        state: str,
        coalition: list[int],
        op: str,
        left_possible: set[str],
        right_possible: set[str] | None,
    ) -> bool:
        """Check the sole profile of total cost |coalition|, independently of enumeration.

        Under the implemented NatATL strategy convention, every agent must end
        with (T*, IDLE) of cost 1. At total cost |coalition| there can be no
        earlier guards. Hence this is the only possible collective profile.
        The upper valuation makes refutation sound even for nested modalities.
        """
        fallback = [
            {"condition_action_pairs": [("T*", "IDLE")]}
            for _ in coalition
        ]
        try:
            product = build_validated_recall_product(
                cgs, coalition, fallback, initial_state=state, context=context
            )
        except InappropriateRecallRule:
            # The sole possible profile is inadmissible, hence none can win.
            return True
        left_product = {
            node for node in product.successors if node.state in left_possible
        }
        right_product = (
            {node for node in product.successors if node.state in right_possible}
            if right_possible is not None else None
        )
        return not check_initial(product, op, left_product, right_product)

    def checked(yes: set[str] | frozenset[str], no: set[str] | frozenset[str]) -> Evidence:
        yes_set, no_set = frozenset(yes), frozenset(no)
        if yes_set & no_set or not yes_set <= universe or not no_set <= universe:
            raise AssertionError("Overlapping or invalid truth certificates")
        return Evidence(yes_set, no_set)

    def evaluate(node: Any) -> Evidence:
        try:
            if node in cache:
                return cache[node]
        except TypeError as exc:
            raise ValueError("Malformed unhashable NatATL AST") from exc

        if isinstance(node, str):
            if node.lower() == "true":
                result = checked(universe, set())
            elif node.lower() == "false":
                result = checked(set(), universe)
            elif node in atomic_props:
                yes = {state for state in states if node in labels[state]}
                result = checked(yes, universe - yes)
            else:
                raise ValueError(f"Unknown atomic proposition {node!r}")
        elif isinstance(node, tuple) and node and isinstance(node[0], str):
            head = node[0]
            upper = head.upper()
            if upper in _NOT:
                if len(node) != 2:
                    raise ValueError("Malformed negation in NatATL AST")
                child = evaluate(node[1])
                result = checked(child.false, child.true)
            elif upper in (_AND | _OR | _IMP):
                if len(node) != 3:
                    raise ValueError("Malformed Boolean connective in NatATL AST")
                left, right = evaluate(node[1]), evaluate(node[2])
                if upper in _AND:
                    result = checked(left.true & right.true, left.false | right.false)
                elif upper in _OR:
                    result = checked(left.true | right.true, left.false & right.false)
                else:
                    result = checked(left.false | right.true, left.true & right.false)
            else:
                m = _MODAL.fullmatch(head)
                if not m:
                    raise ValueError(f"Invalid NatATL AST operator {head!r}")
                op = _OPS.get(m.group("op").upper())
                if op is None:
                    raise ValueError(f"Unsupported NatATL modal operator {m.group('op')!r}")
                if len(node) != (3 if op in {"U", "W"} else 2):
                    raise ValueError(f"Incorrect operands for modal operator {op}")
                coalition = [int(a) for a in m.group("agents").split(",")]
                if not coalition or len(set(coalition)) != len(coalition) or any(
                    a < 1 or a > n_agents for a in coalition
                ):
                    raise ValueError("Invalid coalition in NatATL modality")
                context.require_idle(coalition)
                bound = int(m.group("bound"))
                left = evaluate(node[1])
                right = evaluate(node[2]) if op in {"U", "W"} else None
                # Monotonicity of X/F/G/U/W gives lower and upper operand
                # valuations: true is guaranteed, complement(false) is possible.
                # The latter is essential when proving NEGATIVE nested formulas.
                left_possible = set(universe - left.false)
                right_possible = (
                    set(universe - right.false) if right is not None else None
                )
                yes: set[str] = set()
                no: set[str] = set()
                if complete_supported_grammar:
                    # Structural induction on the AST: every child must already
                    # be decided before its exact truth sets become operands.
                    if left.true | left.false != universe or (
                        right is not None and right.true | right.false != universe
                    ):
                        raise AssertionError(
                            "A child of complete Recall checking is not two-valued"
                        )
                for state in states:
                    # Exact negative certificates independent of regex generation.
                    if bound < len(coalition):
                        no.add(state)
                        refutations[(node, state)] = (bound, "BOUND_BELOW_MINIMUM_COST")
                        continue
                    if op == "F" and not (reachable(state) & left_possible):
                        no.add(state)
                        refutations[(node, state)] = (bound, "GOAL_UNREACHABLE_IN_CGS")
                        continue

                    search = solve_bounded_recall(
                        cgs, coalition, bound, op, left.true,
                        right.true if right is not None else None,
                        initial_state=state,
                        generator=generator,
                        certify_restricted_exhaustion=complete_supported_grammar,
                        context=context,
                    )
                    if search["Satisfiability"] is True:
                        yes.add(state)
                        witnesses[(node, state)] = search
                    elif search["Satisfiability"] is False:
                        if not complete_supported_grammar:
                            raise AssertionError(
                                "Uncertified negative returned by Recall generator"
                            )
                        no.add(state)
                        refutations[(node, state)] = (
                            bound, "EXHAUSTIVE_BOUNDED_RECALL_ENUMERATION"
                        )
                    elif complete_supported_grammar:
                        raise AssertionError(
                            "Exhaustive extended Recall enumeration was undecided"
                        )
                    elif bound == len(coalition) and minimal_profile_loses(
                        state, coalition, op, left_possible, right_possible
                    ):
                        no.add(state)
                        refutations[(node, state)] = (bound, "ONLY_MINIMAL_PROFILE_LOSES")
                    # Otherwise exhaustion provides no negative certificate.
                result = checked(yes, no)
        else:
            raise ValueError("Invalid NatATL AST node")

        cache[node] = result
        return result

    evidence = evaluate(ast)
    if complete_supported_grammar and evidence.true | evidence.false != universe:
        raise AssertionError("Complete Recall evaluation returned undecided states")
    answer = True if start in evidence.true else False if start in evidence.false else None
    status = "VERIFIED_TRUE" if answer is True else "VERIFIED_FALSE" if answer is False else "INCONCLUSIVE"
    output: dict[str, Any] = {
        "Satisfiability": answer,
        "Status": status,
        "initial_state": f"Initial state {start}: {answer if answer is not None else 'Inconclusive'}",
        "res": ("Result: " + ("{" + ", ".join(repr(s) for s in sorted(evidence.true)) + "}"
                              if evidence.true else "set()")),
        "Appropriateness": "global",
        "State Set Complete": evidence.true | evidence.false == universe,
        "Proven True States": sorted(evidence.true),
        "Undecided States": sorted(universe - evidence.true - evidence.false),
        "Search Statistics": dict(context.stats),
        "State Verdicts": {
            state: ("TRUE" if state in evidence.true else "FALSE" if state in evidence.false else "INCONCLUSIVE")
            for state in states
        },
        "Search Scope": f"{generator}_recall_fragment",
        "Supported Grammar Complete": complete_supported_grammar,
        "Full Language Complete": False,
    }
    if (ast, start) in witnesses:
        witness = witnesses[(ast, start)]
        output["Winning Strategy per agent"] = witness["Winning Strategy per agent"]
        output["Complexity Bound"] = witness["Complexity Bound"]
        output["Witness Complexity"] = witness["Witness Complexity"]
    elif (ast, start) in refutations:
        cost, reason = refutations[(ast, start)]
        output["Complexity Bound"] = cost
        output["Negative Certificate"] = reason
    return output


def check_compositional_recall(
    cgs: Any,
    formula: str,
    *,
    initial_state: str | None = None,
    generator: str = "canonical",
    complete_supported_grammar: bool = False,
) -> dict[str, Any]:
    """Parse a textual NatATL formula using VITAMIN's native parser."""
    if not isinstance(formula, str) or not formula.strip():
        raise ValueError("NatATL formula must be a nonempty string")
    # Lazy import makes AST-level evaluation independently testable.
    from model_checker.algorithms.explicit.NatATL.natatl_ast import (
        parse_natatl_formula,
    )

    ast = parse_natatl_formula(formula, cgs.get_number_of_agents())
    return check_compositional_recall_ast(
        cgs, ast, initial_state=initial_state, generator=generator,
        complete_supported_grammar=complete_supported_grammar,
    )
