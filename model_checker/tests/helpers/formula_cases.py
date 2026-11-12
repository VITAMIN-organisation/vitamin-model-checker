"""Each logic's prefix and operators, and one way to parse in any logic, for the cross-logic parser tests."""

import re

from model_checker.parsers.formula_parser_factory import FormulaParserFactory

# logic -> (text before the operator, the unary operator)
OPERATOR_FORMS = {
    "LTL": ("", "F"),
    "CTL": ("", "AF"),
    "ICTL": ("", "AF"),
    "TCTL": ("", "AF"),
    "ATL": ("<1>", "F"),
    "ATLF": ("<1>", "F"),
    "IATL": ("<1>", "F"),
    "ATL_STAR": ("<<1>> ", "F"),
    "Wallet_ATL": ("<<1>>", "F"),
    "OATL": ("<1><2>", "F"),
    "COTL": ("<1><2>", "F"),
    "RBATL": ("<1><2>", "F"),
    "RABATL": ("<1><2>", "F"),
    "NatATL": ("<{1}, 2>", "F"),
    "NatATL_Recall": ("<{1}, 2>", "F"),
    "NatATLF": ("<{1}, 2>", "F"),
    "CapATL": ("<{1}>", "F"),
    "OL": ("<J1>", "F"),
    "TOL": ("{J1}", "F"),
    "NatSL": ("E{1}x: (x, 1) ", "F"),
}

# logic -> binary operators it has (NatSL's one goal has none)
BINARY_OPERATORS = {
    "LTL": ("U",),
    "CTL": ("U",),
    "ICTL": ("U", "R"),
    "TCTL": ("U",),
    "ATL": ("U",),
    "ATLF": ("U",),
    "IATL": ("U", "R"),
    "ATL_STAR": ("U",),
    "Wallet_ATL": ("U",),
    "OATL": ("U", "R", "W"),
    "COTL": ("U", "R", "W"),
    "RBATL": ("U",),
    "RABATL": ("U",),
    "NatATL": ("U",),
    "NatATL_Recall": ("U",),
    "NatATLF": ("U",),
    "CapATL": ("U", "R"),
    "OL": ("U", "R", "W"),
    "TOL": ("U", "R", "W"),
    "NatSL": (),
}

# The CTL family writes a binary operator inside the path quantifier's brackets.
_BINARY_WRAP = {"CTL": "A[{}]", "ICTL": "A[{}]", "TCTL": "A({})"}

# Logics whose formulas take connectives (NatSL goals take none).
CONNECTIVE_LOGICS = sorted(set(OPERATOR_FORMS) - {"NatSL"})


def unary(logic: str, operand: str) -> str:
    """`operand` under the logic's prefix and unary operator, e.g. `<1>F (p && q)`."""
    prefix, op = OPERATOR_FORMS[logic]
    return f"{prefix}{op} {operand}"


def quantified(logic: str, op: str, operand: str) -> str:
    """`operand` under the logic's prefix and the unary operator `op` (`F` or
    `eventually`); the CTL family writes `A F p`, so a word can follow `A`."""
    prefix, default = OPERATOR_FORMS[logic]
    if default == "AF":
        prefix = "A "
    return f"{prefix}{op} {operand}"


def negated(logic: str, negation: str) -> str:
    """`!` or `not` before the logic's unary formula on `p`: NatSL negates its one
    goal after the prefix (`... not F p`), the others negate the operand."""
    prefix, op = OPERATOR_FORMS[logic]
    if logic == "NatSL":
        return f"{prefix}{negation} {op} p"
    return unary(logic, f"{negation} p")


def binary(logic: str, body: str) -> str:
    """Put a binary body such as `p U q` after the logic's prefix, or inside its brackets."""
    if logic in _BINARY_WRAP:
        return _BINARY_WRAP[logic].format(body)
    return f"{OPERATOR_FORMS[logic][0]}{body}"


def parse(logic: str, text: str, n_agent: int = 2):
    """Parse `text` in `logic`; None when the parser rejects it. NatSL takes no agent count."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    try:
        if logic == "NatSL":
            return parser.parse(text)
        return parser.parse(text, n_agent=n_agent)
    except ValueError:
        return None


def parse_errors(logic: str, text: str, n_agent: int = 2) -> list[str]:
    """The parser's errors for `text`, which must be rejected."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    assert parser.parse(text, n_agent=n_agent) is None, f"{logic} accepted '{text}'"
    return parser.errors


def holds_word(result, word: str) -> bool:
    """True when `word` appears as a whole word in the parse tree."""
    return re.search(rf"\b{re.escape(word)}\b", repr(result)) is not None
