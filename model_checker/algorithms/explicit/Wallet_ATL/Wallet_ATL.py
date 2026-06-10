"""Wallet_ATL model checker.

This module ports Wallet_ATL to the same explicit-algorithm structure used by ATL:
- parser via FormulaParserFactory
- tree building via engine.runner.build_formula_tree
- operator solving via dedicated solver/operators modules
- execution wrapper via engine.runner.execute_model_checking_with_parser
"""

import re
from typing import Any, Dict, List

from model_checker.algorithms.explicit.ATL.preimage import (
    build_transition_cache,
)
from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    resolve_atom,
    verify_initial_state,
)
from model_checker.engine.runner import bind_model_checking, build_formula_tree
from model_checker.parsers.formula_parser_factory import FormulaParserFactory

from .solver import solve_tree

_UNARY_OPERATOR_MAP = {
    "!": "!",
    "not": "!",
    "X": "X",
    "next": "X",
    "F": "F",
    "eventually": "F",
    "G": "G",
    "globally": "G",
    "always": "G",
}
_BINARY_OPERATOR_MAP = {
    "or": "||",
    "||": "||",
    "|": "||",
    "and": "&&",
    "&&": "&&",
    "&": "&&",
    "->": "->",
    "implies": "->",
    ">": "->",
    "U": "U",
    "until": "U",
}
_COALITION_TEMPORAL_UNARY = {"X", "F", "G"}


def _normalize_operator(operator: Any) -> str:
    op = str(operator).strip()
    if op in _UNARY_OPERATOR_MAP:
        return _UNARY_OPERATOR_MAP[op]
    if op in _BINARY_OPERATOR_MAP:
        return _BINARY_OPERATOR_MAP[op]
    raise ValueError(f"Unsupported operator '{operator}' in Wallet_ATL formula")


def _serialize_constraints(constraints: List[Dict[str, Any]]) -> str:
    serialized = []
    for item in constraints:
        agent = int(item["agent"])
        operator = str(item["operator"]).strip()
        value = int(item["value"])
        serialized.append(f"wallet({agent},{operator}{value})")
    return "&&".join(serialized)


def _build_coalition_prefix(
    agents: List[int], constraints: List[Dict[str, Any]]
) -> str:
    if not agents:
        raise ValueError("Wallet_ATL coalition cannot be empty")

    coalition = ",".join(str(int(agent)) for agent in agents)
    if constraints:
        return f"<<{coalition}:{_serialize_constraints(constraints)}>>"
    return f"<<{coalition}>>"


def _convert_wallet_ast(node: Any) -> Any:
    """Convert Wallet_ATL parser dict-AST to tuple-AST used by explicit solvers."""
    if isinstance(node, tuple):
        return tuple(_convert_wallet_ast(part) for part in node)

    if isinstance(node, str):
        return node

    if not isinstance(node, dict):
        raise ValueError("Invalid Wallet_ATL AST node")

    node_type = node.get("type")

    if node_type == "proposition":
        proposition = node.get("proposition")
        if proposition is None:
            raise ValueError("Invalid proposition node in Wallet_ATL AST")
        return str(proposition)

    if node_type == "unary":
        operator = _normalize_operator(node.get("operator"))
        operand = _convert_wallet_ast(node.get("formula"))
        return (operator, operand)

    if node_type == "binary":
        operator = _normalize_operator(node.get("operator"))
        left = _convert_wallet_ast(node.get("left"))
        right = _convert_wallet_ast(node.get("right"))
        return (operator, left, right)

    if node_type in ("coalition", "coalition_wallet"):
        agents = node.get("agents", [])
        constraints = node.get("constraints", [])
        inner_formula = node.get("formula")

        if not isinstance(inner_formula, dict):
            raise ValueError("Invalid coalition formula in Wallet_ATL AST")

        coalition_prefix = _build_coalition_prefix(agents, constraints)
        inner_type = inner_formula.get("type")

        if inner_type == "unary":
            operator = _normalize_operator(inner_formula.get("operator"))
            if operator not in _COALITION_TEMPORAL_UNARY:
                raise ValueError(
                    "Wallet_ATL coalition formulas must use X, F, or G temporal operators"
                )
            operand = _convert_wallet_ast(inner_formula.get("formula"))
            return (coalition_prefix + operator, operand)

        if inner_type == "binary":
            operator = _normalize_operator(inner_formula.get("operator"))
            if operator != "U":
                raise ValueError(
                    "Wallet_ATL coalition binary formulas must use the U temporal operator"
                )
            left = _convert_wallet_ast(inner_formula.get("left"))
            right = _convert_wallet_ast(inner_formula.get("right"))
            return (coalition_prefix + "U", left, right)

        raise ValueError(
            "Wallet_ATL coalition formulas require a temporal body (X, F, G, or U)"
        )

    raise ValueError(f"Unsupported Wallet_ATL AST node type '{node_type}'")


def _extract_state_name(initial_state: str) -> str:
    """Extract plain state name from wallet-extended state IDs (e.g. s9:10:20)."""
    match = re.match(r"^(s\d+)", str(initial_state).strip())
    return match.group(1) if match else str(initial_state).strip()


def _core_walletatl_checking(cgs, formula: str) -> Dict[str, Any]:
    """Core Wallet_ATL model checking logic."""
    from model_checker.utils.error_handler import (
        create_semantic_error,
        create_syntax_error,
    )

    parser = FormulaParserFactory.get_parser_instance("Wallet_ATL")
    res_parsing = parser.parse(formula, max_coalition=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    try:
        normalized_ast = _convert_wallet_ast(res_parsing)
    except ValueError as exc:
        return create_syntax_error(str(exc))

    root = build_formula_tree(
        normalized_ast,
        lambda atom: resolve_atom(cgs, atom),
    )
    if root is None:
        return create_semantic_error("One or more atoms do not exist in the model")

    transition_cache = build_transition_cache(cgs)
    solve_tree(cgs, root, transition_cache)

    initial_state = cgs.initial_state
    state_name = _extract_state_name(initial_state)
    is_satisfied = verify_initial_state(state_name, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = bind_model_checking("Wallet_ATL", _core_walletatl_checking)
