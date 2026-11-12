"""NatATL formula parsing and AST utilities for the memoryless/recall hot path."""

import re
from typing import Any

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.syntax_patterns import OPERATOR_WORDS, spelling_to_symbol

# The parser keeps a connective as written (`and` or `&&`); temporal operators
# reach the AST as their symbol (`eventually` is `F`), which CTL takes as is.
_CTL_BINARY_OPS = spelling_to_symbol("AND", "OR", "IMPLIES")
_CTL_UNARY_NOT = frozenset(spelling_to_symbol("NOT"))
_TEMPORAL_SYMBOLS = "".join(
    OPERATOR_WORDS[token].symbol
    for token in ("NEXT", "EVENTUALLY", "GLOBALLY", "UNTIL")
)
_COALITION_MODAL_RE = re.compile(
    rf"^<\{{(?P<agents>[\d,]+)\}},\s*(?P<k>\d+)>(?P<op>[{_TEMPORAL_SYMBOLS}])$"
)


def parse_natatl_formula(formula: str, n_agent: int) -> Any:
    """Parse a NatATL formula as written: ``Fp`` is one word (an invalid name), not ``F p``."""
    parser = FormulaParserFactory.get_parser_instance("NatATL")
    ast = parser.parse(formula.strip(), n_agent=n_agent)
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


def get_agents_from_ast(ast: Any) -> list[int]:
    """Collect sorted agent indices referenced in coalition modalities."""
    agents: set[int] = set()
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


def _ctl_operand(ast: Any) -> str:
    """An operand, in parentheses when it is a coalition formula: CTL refuses
    `A F p && q` as ambiguous, so `(A F p) && q` must be written out. Connectives
    and negations bring their own parentheses."""
    text = natatl_ast_to_ctl(ast)
    is_modal = isinstance(ast, tuple) and _COALITION_MODAL_RE.match(str(ast[0]))
    return f"({text})" if is_modal else text


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
        return f"({_ctl_operand(ast[1])} {op} {_ctl_operand(ast[2])})"

    if isinstance(head, str):
        match = _COALITION_MODAL_RE.match(head)
        if match:
            op_letter = match.group("op")
            if len(ast) == 2:
                child = natatl_ast_to_ctl(ast[1])
                return f"A {op_letter} {child}"
            if len(ast) == 3 and op_letter == "U":
                return f"A ({_ctl_operand(ast[1])} U {_ctl_operand(ast[2])})"

    raise ValueError("Invalid NatATL AST structure for CTL conversion")


def analyze_natatl_formula(
    formula: str, n_agent: int
) -> tuple[Any, str, list[int], int]:
    """Parse NatATL and return (ast, ctl_formula, agents, k)."""
    ast = parse_natatl_formula(formula, n_agent)
    ctl_formula = natatl_ast_to_ctl(ast)
    parser = FormulaParserFactory.get_parser_instance("CTL")
    if parser.parse(ctl_formula) is None:
        detail = parser.errors[0] if parser.errors else "syntactically invalid"
        raise ValueError(f"Resulting CTL formula '{ctl_formula}' is {detail}")
    return ast, ctl_formula, get_agents_from_ast(ast), get_k_value_from_ast(ast)
