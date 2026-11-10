from typing import Any

from model_checker.parsers.formula_parser_factory import FormulaParserFactory

# The parser keeps the spelling the user wrote (`and`, `NEXT`), so map each spelling
# to one symbol.
_SYMBOL = {
    "!": "!",
    "NOT": "!",
    "&&": "&&",
    "AND": "&&",
    "||": "||",
    "OR": "||",
    "->": "->",
    "IMPLIES": "->",
    "X": "X",
    "NEXT": "X",
    "F": "F",
    "EVENTUALLY": "F",
    "G": "G",
    "GLOBALLY": "G",
    "U": "U",
    "UNTIL": "U",
}
_CONNECTIVES = ("&&", "||", "->")


def _symbol(node: Any) -> str | None:
    return None if isinstance(node, str) else _SYMBOL[node[0].upper()]


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
    """Adapt an LTL formula string for the CTL-backed sure-win checker.

    Turns the user formula into a universally quantified CTL-shaped string that
    the CTL parser accepts after strategy pruning. This is a syntactic bridge
    for VITAMIN's strategic LTL mode, not a classical LTL-to-CTL embedding.
    """
    parser = FormulaParserFactory.get_parser_instance("LTL")
    ast = parser.parse(ltl_formula)
    if ast is None:
        raise ValueError(f"Invalid LTL formula {ltl_formula!r}: {parser.errors[0]}")
    return _render(ast)
