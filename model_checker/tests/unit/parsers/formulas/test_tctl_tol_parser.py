"""TCTL and TOL: clock constraints, freeze, constants, and the errors only they have.

Both lex `x>5` as a clock constraint, so `>` must never be mistaken for the
rejected implication alias. TCTL has no next operator (IC 1993, p. 10).
"""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas import TCTL, TOL


def _parse(logic: str, formula: str):
    return FormulaParserFactory.get_parser_instance(logic).parse(formula)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("logic", "module", "formula"),
    [("TCTL", TCTL, "j.p"), ("TOL", TOL, "j.goal")],
)
def test_freeze_binds_the_clock_name(logic, module, formula):
    """`j.p` freezes clock j over p."""
    tree = _parse(logic, formula)
    assert isinstance(tree, module.FreezeExpr)
    assert tree.clock == "j"


@pytest.mark.unit
@pytest.mark.parametrize(("logic", "module"), [("TCTL", TCTL), ("TOL", TOL)])
@pytest.mark.parametrize("constraint", ["x>5", "x>=5", "x<5", "x<=5"])
def test_clock_comparison_is_one_time_atom(logic, module, constraint):
    """`x>5` is a constraint on clock x, not `x` and something after `>`."""
    tree = _parse(logic, constraint)
    assert isinstance(tree, module.SimpleTimeExpr)
    assert tree.constraints == constraint


@pytest.mark.unit
def test_implication_is_not_a_clock_comparison():
    """`p -> q` is an implication of two propositions."""
    tree = _parse("TCTL", "p -> q")
    assert isinstance(tree, TCTL.Binary)
    assert tree.op == "->"
    assert (tree.left.name, tree.right.name) == ("p", "q")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("logic", "module", "formula", "value"),
    [
        ("TCTL", TCTL, "true", True),
        ("TCTL", TCTL, "false", False),
        ("TOL", TOL, "true", True),
        ("TOL", TOL, "false", False),
        ("TOL", TOL, "@", True),
        ("TOL", TOL, "#", False),
    ],
)
def test_constants_are_not_propositions(logic, module, formula, value):
    """`true` and TOL's `@` are the constant, not an atom a model could label."""
    tree = _parse(logic, formula)
    assert isinstance(tree, module.BooleanConst)
    assert tree.value is value


@pytest.mark.unit
@pytest.mark.parametrize("logic", ["CTL", "ICTL", "TCTL"])
@pytest.mark.parametrize(
    ("wordy", "compact"), [("forall G p", "AG p"), ("exist F p", "EF p")]
)
def test_forall_and_exist_are_the_path_quantifiers(logic, wordy, compact):
    """`forall G p` is `AG p`."""
    tree = _parse(logic, wordy)
    assert tree is not None
    assert repr(tree) == repr(_parse(logic, compact))


@pytest.mark.unit
@pytest.mark.parametrize("operator", ["R", "W"])
def test_tol_release_and_weak_until_take_optional_parentheses(operator):
    """`{J2} p R q` and `{J2} (p R q)` are one formula (Until is in test_until_after_prefix)."""
    flat = _parse("TOL", f"{{J2}} p {operator} q")
    assert flat is not None
    assert repr(flat) == repr(_parse("TOL", f"{{J2}} (p {operator} q)"))


@pytest.mark.unit
@pytest.mark.parametrize(
    ("logic", "formula", "prefix", "connective", "position"),
    [
        ("TCTL", "AF p && q", "AF", "&&", 0),
        ("TCTL", "AF (p) && q", "AF", "&&", 0),
        ("TCTL", "r && x. p && q", "x.", "&&", 5),
        ("TCTL", "AF p : x<5 && q", "AF", "&&", 0),
        ("TOL", "{J2}X p || q", "{J2}X", "||", 0),
        ("TOL", "j. p && q", "j.", "&&", 0),
    ],
)
def test_ambiguity_error_names_the_prefix_and_both_readings(
    logic, formula, prefix, connective, position
):
    """Freeze `x.` is a prefix too; the message shows where and both groupings."""
    parser = FormulaParserFactory.get_parser_instance(logic)
    assert parser.parse(formula) is None
    [error] = parser.errors
    assert f"position {position}" in error
    assert f"{prefix} (... {connective} ...)" in error
    assert f"({prefix} ...) {connective} ..." in error


@pytest.mark.unit
@pytest.mark.parametrize(
    ("formula", "named"),
    [
        ("AX p", "'AX' at position 1"),
        ("EX p", "'EX' at position 1"),
        ("X p", "'X' at position 1"),
        ("AG (p -> AX q)", "'AX' at position 10"),
        ("A next p", "'A next' at position 1"),
    ],
)
def test_tctl_has_no_next_operator(formula, named):
    """Time is dense, so there is no next state; the error names the operator."""
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    assert parser.parse(formula) is None
    [error] = parser.errors
    assert error.startswith(f"TCTL has no next operator ({named})"), error
