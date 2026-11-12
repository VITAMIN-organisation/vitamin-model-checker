from typing import Any

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.syntax_patterns import spelling_to_symbol

# The parser keeps the spelling of a connective (`and` or `&&`), so map each
# spelling to one symbol.
_SYMBOL = spelling_to_symbol(
    "NOT", "AND", "OR", "IMPLIES", "NEXT", "EVENTUALLY", "GLOBALLY", "UNTIL"
)
_CONNECTIVES = ("&&", "||", "->")


def _symbol(node: Any) -> str | None:
    return None if isinstance(node, str) else _SYMBOL[node[0]]


def _operand(node: Any) -> str:
    """Render an operand of a connective or Until, in parentheses unless it is a name or an Until."""
    text = _render(node)
    return text if _symbol(node) in (None, "U") else f"({text})"


def _render(node: Any) -> str:
    symbol = _symbol(node)
    if symbol is None:
        return node
    if symbol == "U":
        return f"A({_operand(node[1])} U {_operand(node[2])})"
    if len(node) == 3:
        return f"{_operand(node[1])} {symbol} {_operand(node[2])}"
    child = node[1]
    body = _operand(child) if _symbol(child) in _CONNECTIVES else _render(child)
    return f"!{body}" if symbol == "!" else f"A{symbol} {body}"


def ltl_to_ctl(ltl_formula: str) -> str:
    """Rewrite an LTL formula as the A-quantified CTL text the sure-win checker uses;
    a syntactic bridge, not a real LTL-to-CTL translation."""
    parser = FormulaParserFactory.get_parser_instance("LTL")
    ast = parser.parse(ltl_formula)
    if ast is None:
        raise ValueError(f"Invalid LTL formula {ltl_formula!r}: {parser.errors[0]}")
    return _render(ast)
