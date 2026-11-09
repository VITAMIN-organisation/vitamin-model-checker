"""TCTL and TOL parsers: clock ops, booleans, freeze, and quantifier aliases."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.TCTL import (
    AtomicProp,
    Binary,
    BooleanConst,
    FreezeExpr,
    QuantifiedPath,
    SimpleTimeExpr,
)
from model_checker.parsers.formulas.TOL import (
    BooleanConst as TolBooleanConst,
)
from model_checker.parsers.formulas.TOL import (
    FreezeExpr as TolFreezeExpr,
)
from model_checker.parsers.formulas.TOL import (
    SimpleTimeExpr as TolSimpleTimeExpr,
)


@pytest.mark.unit
def test_tctl_parser_freeze_expression():
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    ast = parser.parse("j.p")
    assert isinstance(ast, FreezeExpr)
    assert ast.clock == "j"


@pytest.mark.unit
def test_tctl_parser_parenthesized_until_matches_flat():
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    flat = parser.parse("E p U q")
    grouped = parser.parse("E (p U q)")
    assert isinstance(flat, QuantifiedPath)
    assert isinstance(grouped, QuantifiedPath)
    assert flat.quantifier == grouped.quantifier == "E"
    assert isinstance(flat.formula, Binary)
    assert repr(flat.formula) == repr(grouped.formula)


@pytest.mark.unit
def test_tctl_parser_mixed_case_atom_is_not_a_quantifier():
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    ast = parser.parse("Goal")
    assert isinstance(ast, AtomicProp)
    assert ast.name == "Goal"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("x>5", "x>5"),
        ("x>=5", "x>=5"),
        ("x<5", "x<5"),
        ("x<=5", "x<=5"),
    ],
)
def test_tctl_clock_comparison_is_time_atom_not_implies(formula, expected):
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    ast = parser.parse(formula)
    assert isinstance(ast, SimpleTimeExpr)
    assert ast.constraints == expected


@pytest.mark.unit
def test_tctl_implication_is_not_a_clock_greater_than():
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    ast = parser.parse("p -> q")
    assert isinstance(ast, Binary)
    assert ast.op in {"->", "implies"}
    assert isinstance(ast.left, AtomicProp)
    assert isinstance(ast.right, AtomicProp)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("formula", "value"),
    [("true", True), ("false", False)],
)
def test_tctl_boolean_constants_are_not_propositions(formula, value):
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    ast = parser.parse(formula)
    assert isinstance(ast, BooleanConst)
    assert ast.value is value


@pytest.mark.unit
@pytest.mark.parametrize(
    ("wordy", "compact"),
    [
        ("forall G p", "AG p"),
        ("exist F p", "EF p"),
    ],
)
def test_tctl_parser_forall_exist_keywords(wordy, compact):
    parser = FormulaParserFactory.get_parser_instance("TCTL")
    wordy_ast = parser.parse(wordy)
    compact_ast = parser.parse(compact)
    assert isinstance(wordy_ast, QuantifiedPath)
    assert isinstance(compact_ast, QuantifiedPath)
    assert repr(wordy_ast) == repr(compact_ast)


@pytest.mark.unit
def test_tol_parser_freeze_expression():
    parser = FormulaParserFactory.get_parser_instance("TOL")
    ast = parser.parse("j.Goal")
    assert isinstance(ast, TolFreezeExpr)
    assert ast.clock == "j"


@pytest.mark.unit
def test_tol_clock_greater_than_is_time_atom():
    parser = FormulaParserFactory.get_parser_instance("TOL")
    ast = parser.parse("x>5")
    assert isinstance(ast, TolSimpleTimeExpr)
    assert ast.constraints == "x>5"


@pytest.mark.unit
@pytest.mark.parametrize("operator", ["R", "W"])
def test_tol_release_and_weak_until_take_optional_parentheses(operator):
    # Until is covered for every prefix logic in test_until_after_prefix.py.
    parser = FormulaParserFactory.get_parser_instance("TOL")
    flat = parser.parse(f"{{J2}} p {operator} q")
    grouped = parser.parse(f"{{J2}} (p {operator} q)")
    assert flat is not None
    assert repr(flat) == repr(grouped)


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
    parser = FormulaParserFactory.get_parser_instance(logic)
    assert parser.parse(formula) is None
    [error] = parser.errors
    assert f"position {position}" in error
    assert f"{prefix} (... {connective} ...)" in error
    assert f"({prefix} ...) {connective} ..." in error


@pytest.mark.unit
@pytest.mark.parametrize(
    ("logic", "formula"),
    [
        ("TCTL", "AG (p -> EF q)"),
        ("TCTL", "AG AF p"),
        ("TCTL", "j.(p && q)"),
        ("TOL", "j.{J2}F p"),
    ],
)
def test_freeze_and_nested_prefixes_parse(logic, formula):
    parser = FormulaParserFactory.get_parser_instance(logic)
    assert parser.parse(formula) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("formula", "value"),
    [("true", True), ("false", False), ("@", True), ("#", False)],
)
def test_tol_boolean_constants_and_hash_at(formula, value):
    parser = FormulaParserFactory.get_parser_instance("TOL")
    ast = parser.parse(formula)
    assert isinstance(ast, TolBooleanConst)
    assert ast.value is value
