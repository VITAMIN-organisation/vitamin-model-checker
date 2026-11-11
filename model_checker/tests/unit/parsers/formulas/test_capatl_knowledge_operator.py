"""CapATL knowledge operator K^a_cap(phi), typed `K1(...)` or `kcap1(...)`.

The grammar is AAMAS 2024 p. 125: `K^a_cap(phi)` with phi ::= a -> c | !phi |
phi && phi; p. 126 adds ||, -> and true/false as sugar. The parentheses are part
of the rule, and phi holds no proposition and no K.
"""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


def _parse(formula):
    parser = FormulaParserFactory.get_parser_instance("CapATL")
    return parser.parse(formula, n_agent=3), parser.errors


@pytest.mark.parametrize(
    ("formula", "tree"),
    [
        ("K1(1 is c)", ("K1", ("is", "1", "c"))),
        ("kcap1(1 is c)", ("K1", ("is", "1", "c"))),
        ("K01(1 is c)", ("K1", ("is", "1", "c"))),
        ("<{1}> F K2(3 is c1)", ("<{1}>F", ("K2", ("is", "3", "c1")))),
        (
            "<{1}> F (gray && K2(3 is c1 || 3 is c2))",
            (
                "<{1}>F",
                (
                    "&&",
                    "gray",
                    ("K2", ("||", ("is", "3", "c1"), ("is", "3", "c2"))),
                ),
            ),
        ),
        (
            "K2(!(3 is c1) && true)",
            ("K2", ("&&", ("!", ("is", "3", "c1")), "true")),
        ),
    ],
)
def test_paper_forms_parse(formula, tree):
    """`K1(...)` and `kcap1(...)` build one K node; `K01` reads agent 1."""
    result, errors = _parse(formula)
    assert result == tree, errors


@pytest.mark.parametrize(
    ("formula", "message"),
    [
        ("K1 1 is c", "'K1' needs parentheses"),
        ("<{1}> F (K2(K3(1 is c)))", "K3(...) inside a capacity formula"),
        ("<{1}> F (K2(p))", "'p' inside K(...)"),
        ("<{1}> F (K4(1 is c))", "Agent 4 in 'K4'"),
        ("<{1}> F (K1(4 is c))", "Agent 4 in '4 is c'"),
        ("K1(1 IS c)", "Syntax error near token 'IS'"),
    ],
)
def test_forms_outside_the_paper_are_rejected_with_a_message(formula, message):
    """No parentheses, a nested K, a proposition inside K, an agent out of range,
    or `is` not in lowercase (word operators are lowercase only)."""
    result, errors = _parse(formula)
    assert result is None
    assert any(message in error for error in errors), errors


@pytest.mark.parametrize("name", ["K1x", "K12x", "Knowledge"])
def test_k_followed_by_letters_is_a_proposition(name):
    """`K1x` and `Knowledge` are names: K needs digits then a parenthesis."""
    result, errors = _parse(f"<{{1}}> F {name}")
    assert result == ("<{1}>F", name), errors
