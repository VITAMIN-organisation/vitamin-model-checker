
"""Compositional evaluation of NatATL formulas."""

import re
from collections.abc import Callable, Mapping
from typing import Any

MODAL = re.compile(
    r"^<\{(?P<agents>\d*(?:,\d+)*)\},\s*(?P<bound>\d+)>(?P<op>[A-Za-z]+)$",
    re.IGNORECASE,
)

_UNARY = {
    "X": "X", "NEXT": "X",
    "F": "F", "EVENTUALLY": "F",
    "G": "G", "GLOBALLY": "G", "ALWAYS": "G",
}

_BINARY = {
    "U": "U", "UNTIL": "U",
    "W": "W", "WEAK": "W", "WEAKUNTIL": "W",
}


def satisfying_states(
    ast: Any,
    states: set[str],
    valuation: Mapping[str, set[str]],
    modal_states: Callable[
        [tuple[int, ...], int, str, set[str], set[str] | None],
        set[str],
    ],
) -> set[str]:
    """
    Evaluate a NatATL AST bottom-up.

    modal_states(A, k, op, left, right) must return
    the states where coalition A has a winning
    natural strategy of total complexity <= k.
    """
    universe = set(states)

    if any(not set(ss) <= universe for ss in valuation.values()):
        raise ValueError("Valuation references an unknown state")

    memo: dict[str, set[str]] = {}

    def visit(node: Any) -> set[str]:
        key = repr(node)

        if key in memo:
            return memo[key].copy()

        if isinstance(node, str):
            if node.lower() == "true":
                result = universe.copy()
            elif node.lower() == "false":
                result = set()
            elif node in valuation:
                result = set(valuation[node])
            else:
                raise ValueError(
                    f"Unknown atomic proposition: {node!r}"
                )

        elif isinstance(node, tuple) and node:
            head = node[0]

            if not isinstance(head, str):
                raise ValueError("Malformed NatATL AST")

            match = MODAL.fullmatch(head)

            if match:
                agent_text = match.group("agents")
                agents = tuple(
                    int(x) for x in agent_text.split(",") if x
                )
                k = int(match.group("bound"))
                op = match.group("op").upper()

                if len(set(agents)) != len(agents):
                    raise ValueError("Repeated coalition agent")
                if any(a < 1 for a in agents):
                    raise ValueError("Invalid coalition agent")

                if op in _UNARY and len(node) == 2:
                    normalized_op = _UNARY[op]
                    left = visit(node[1])
                    right = None

                elif op in _BINARY and len(node) == 3:
                    normalized_op = _BINARY[op]
                    left = visit(node[1])
                    right = visit(node[2])

                else:
                    raise ValueError(
                        f"Unsupported strategic modality: {node!r}"
                    )

                result = modal_states(
                    agents,
                    k,
                    normalized_op,
                    left,
                    right,
                )

                if not isinstance(result, set) or not result <= universe:
                    raise ValueError(
                        "Strategic backend returned invalid states"
                    )

            elif head.upper() in ("!", "NOT") and len(node) == 2:
                result = universe - visit(node[1])

            elif head.upper() in ("&&", "AND") and len(node) == 3:
                result = visit(node[1]) & visit(node[2])

            elif head.upper() in ("||", "OR") and len(node) == 3:
                result = visit(node[1]) | visit(node[2])

            elif head.upper() in ("->", "IMPLIES", ">") and len(node) == 3:
                result = (universe - visit(node[1])) | visit(node[2])

            else:
                raise ValueError(f"Unsupported NatATL AST: {node!r}")

        else:
            raise ValueError(f"Malformed NatATL AST: {node!r}")

        memo[key] = set(result)
        return memo[key].copy()

    return visit(ast)
