"""TCTL and TOL parsers accept mixed-case atomic propositions."""

import pytest

from model_checker.parsers.formulas.TCTL.tctl_ply_parser import do_parsingTCTL
from model_checker.parsers.formulas.TOL.tol_ply_parser import do_parsing


@pytest.mark.unit
def test_tctl_parser_freeze_expression():
    ast = do_parsingTCTL("j.p")
    assert ast is not None
    from model_checker.parsers.formulas.TCTL.tctl_ply_parser import FreezeExpr

    assert isinstance(ast, FreezeExpr)
    assert ast.clock == "j"


@pytest.mark.unit
def test_tctl_parser_parenthesized_until():
    from model_checker.parsers.formulas.TCTL.tctl_ply_parser import (
        Binary,
        QuantifiedPath,
    )

    flat = do_parsingTCTL("E p U q")
    grouped = do_parsingTCTL("E (p U q)")
    assert flat is not None
    assert grouped is not None
    assert isinstance(flat, QuantifiedPath)
    assert isinstance(grouped, QuantifiedPath)
    assert flat.quantifier == grouped.quantifier == "E"
    assert isinstance(flat.formula, Binary)
    assert repr(flat.formula) == repr(grouped.formula)


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "E (p U q)",
        "A (Goal U safe_1)",
    ],
)
def test_tctl_parser_accepts_parenthesized_until(formula):
    assert do_parsingTCTL(formula) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "Goal",
        "EF Goal",
        "AG Goal",
        "Goal && safe_1",
        "x<=1",
    ],
)
def test_tctl_parser_accepts_mixed_case_propositions(formula):
    assert do_parsingTCTL(formula) is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    "formula",
    [
        "Goal",
        "{J1}F Goal",
        "{J1}G Goal",
        "Goal && safe_1",
        "x<=1",
        "j.Goal",
    ],
)
def test_tol_parser_accepts_mixed_case_propositions(formula):
    assert do_parsing(formula) is not None


@pytest.mark.unit
def test_tol_parser_freeze_expression():
    ast = do_parsing("j.Goal")
    assert ast is not None
    from model_checker.parsers.formulas.TOL.tol_ply_parser import FreezeExpr

    assert isinstance(ast, FreezeExpr)
    assert ast.clock == "j"
