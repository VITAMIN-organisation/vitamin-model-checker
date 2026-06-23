"""NatATL formula parsing and AST utilities for the memoryless/recall hot path."""

import re
from typing import Any, List, Set, Tuple

from model_checker.parsers.formula_parser_factory import FormulaParserFactory

_COALITION_MODAL_RE = re.compile(
    r"^<\{(?P<agents>[\d,]+)\},\s*(?P<k>\d+)>(?P<op>[A-Za-z]+)$",
    re.IGNORECASE,
)
_NATATL_TEMPORAL_GLUE = re.compile(
    r"(<\{[^}]+\},\s*\d+>)([FGXU])([a-zA-Z_])",
    re.IGNORECASE,
)
_CTL_BINARY_OPS = {
    "&&": "&&",
    "AND": "&&",
    "||": "||",
    "OR": "||",
    "->": "->",
    "IMPLIES": "->",
    ">": "->",
}
_CTL_UNARY_NOT = frozenset({"!", "NOT", "not"})


def _normalize_natatl_surface(formula: str) -> str:
    """Insert spaces between coalition temporal letters and propositions when glued."""
    return _NATATL_TEMPORAL_GLUE.sub(r"\1\2 \3", formula.strip())


def parse_natatl_formula(formula: str, n_agent: int) -> Any:
    """Parse a NatATL formula via the registered NatATL parser."""
    parser = FormulaParserFactory.get_parser_instance("NatATL")
    ast = parser.parse(_normalize_natatl_surface(formula), n_agent=n_agent)
    if ast is None:
        detail = parser.errors[0] if parser.errors else "syntactically invalid"
        raise ValueError(f"Invalid NatATL formula: {detail}")
    return ast


def _iter_coalition_modals(ast: Any):
    """Yield (agents_csv, k, op_suffix) for each coalition modality in the AST."""
    if isinstance(ast, str):
        return
    if not isinstance(ast, tuple) or not ast:
        return

    head = ast[0]
    if isinstance(head, str):
        match = _COALITION_MODAL_RE.match(head)
        if match:
            yield match.group("agents"), int(match.group("k")), match.group("op")

    if head in _CTL_UNARY_NOT and len(ast) >= 2:
        yield from _iter_coalition_modals(ast[1])
        return

    if head in _CTL_BINARY_OPS and len(ast) == 3:
        yield from _iter_coalition_modals(ast[1])
        yield from _iter_coalition_modals(ast[2])


def get_agents_from_ast(ast: Any) -> List[int]:
    """Collect sorted agent indices referenced in coalition modalities."""
    agents: Set[int] = set()
    for agents_csv, _, _ in _iter_coalition_modals(ast):
        for part in agents_csv.split(","):
            part = part.strip()
            if part:
                agents.add(int(part))
    if not agents:
        raise ValueError("NatATL formula must use <{agents}, k> syntax")
    return sorted(agents)


def get_k_value_from_ast(ast: Any) -> int:
    """Return the strategy-complexity bound k from the first coalition modality."""
    for _, k, _ in _iter_coalition_modals(ast):
        return k
    raise ValueError("NatATL formula must use <{agents}, k> syntax")


def _normalize_ctl_spacing(ctl_formula: str) -> str:
    ctl_formula = re.sub(r"([AE])([FGXU])", r"\1 \2", ctl_formula)
    return re.sub(r"([FGXU])(?=[a-zA-Z])", r"\1 ", ctl_formula)


def _ctl_temporal_letter(op_suffix: str) -> str:
    op = op_suffix.upper()
    if op in {"F", "EVENTUALLY"}:
        return "F"
    if op in {"G", "GLOBALLY", "ALWAYS"}:
        return "G"
    if op in {"X", "NEXT"}:
        return "X"
    if op in {"U", "UNTIL"}:
        return "U"
    raise ValueError(f"Unsupported NatATL temporal operator: {op_suffix}")


def natatl_ast_to_ctl(ast: Any) -> str:
    """Lower a parsed NatATL AST to a CTL formula string (path quantifier A)."""
    if isinstance(ast, str):
        return ast

    if not isinstance(ast, tuple) or len(ast) < 2:
        raise ValueError("Invalid NatATL AST")

    head = ast[0]

    if head in _CTL_UNARY_NOT:
        return f"!({natatl_ast_to_ctl(ast[1])})"

    if head in _CTL_BINARY_OPS and len(ast) == 3:
        op = _CTL_BINARY_OPS[head]
        left = natatl_ast_to_ctl(ast[1])
        right = natatl_ast_to_ctl(ast[2])
        return f"({left} {op} {right})"

    if isinstance(head, str):
        match = _COALITION_MODAL_RE.match(head)
        if match:
            op_letter = _ctl_temporal_letter(match.group("op"))
            if len(ast) == 2:
                child = natatl_ast_to_ctl(ast[1])
                return _normalize_ctl_spacing(f"A {op_letter} {child}")
            if len(ast) == 3 and op_letter == "U":
                left = natatl_ast_to_ctl(ast[1])
                right = natatl_ast_to_ctl(ast[2])
                return _normalize_ctl_spacing(f"A ({left} U {right})")

    raise ValueError("Invalid NatATL AST structure for CTL conversion")


def analyze_natatl_formula(
    formula: str, n_agent: int
) -> Tuple[Any, str, List[int], int]:
    """Parse NatATL and return (ast, ctl_formula, agents, k)."""
    ast = parse_natatl_formula(formula, n_agent)
    ctl_formula = natatl_ast_to_ctl(ast)
    parser = FormulaParserFactory.get_parser_instance("CTL")
    if parser.parse(ctl_formula) is None:
        detail = parser.errors[0] if parser.errors else "syntactically invalid"
        raise ValueError(f"Resulting CTL formula '{ctl_formula}' is {detail}")
    return ast, ctl_formula, get_agents_from_ast(ast), get_k_value_from_ast(ast)
