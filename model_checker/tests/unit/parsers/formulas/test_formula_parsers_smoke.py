"""Smoke tests: one valid and one invalid formula per logic (covers all formula parsers)."""

import importlib

import pytest

from model_checker.tests.helpers.model_helpers import assert_parse_structure


@pytest.mark.unit
@pytest.mark.parametrize(
    "logic,valid_formula,invalid_formula,n_agent",
    [
        ("ATL", "<1>F p", "<1>F", 2),
        ("CTL", "EF p", "EX", None),
        ("LTL", "F p", "X", None),
        ("NatATL", "<{1}, 1>F p", "<{1}, 1>F", 2),
        ("OATL", "<1><5>F p", "<1>F p", 2),
        ("OL", "<J1>F p", "<J1>F", None),
        ("RBATL", "<1><5>F p", "<1>F p", 2),
        ("NatSL", "E{3}x:(x,1)F a", "E{3}x:Fa", None),
        ("CapATL", "<{1}, 5>X p", "<{1}, 5>X", 2),
    ],
)
def test_formula_parser_valid_and_invalid(
    logic, valid_formula, invalid_formula, n_agent
):
    """Each logic parser accepts one valid formula and rejects one invalid."""
    parser_module = {
        "ATL": ("model_checker.parsers.formulas.ATL.parser", "ATLParser"),
        "CTL": ("model_checker.parsers.formulas.CTL.parser", "CTLParser"),
        "LTL": ("model_checker.parsers.formulas.LTL.parser", "LTLParser"),
        "NatATL": (
            "model_checker.parsers.formulas.NatATL.parser",
            "NatATLParser",
        ),
        "OATL": ("model_checker.parsers.formulas.OATL.parser", "OATLParser"),
        "OL": ("model_checker.parsers.formulas.OL.parser", "OLParser"),
        "RBATL": ("model_checker.parsers.formulas.RBATL.parser", "RBATLParser"),
        "NatSL": ("model_checker.parsers.formulas.NatSL.parser", "NatSLParser"),
        "CapATL": (
            "model_checker.parsers.formulas.CapATL.parser",
            "CapATLParser",
        ),
    }
    mod_path, class_name = parser_module[logic]
    mod = importlib.import_module(mod_path)
    parser_class = getattr(mod, class_name)
    parser = parser_class()
    kwargs = {} if n_agent is None else {"n_agent": n_agent}
    result_valid = parser.parse(valid_formula, **kwargs)
    assert result_valid is not None, f"{logic} valid formula should parse"
    assert_parse_structure(result_valid, description=logic)
    result_invalid = parser.parse(invalid_formula, **kwargs)
    assert result_invalid is None, f"{logic} invalid formula should not parse"


@pytest.mark.unit
@pytest.mark.parametrize(
    "logic,formula_with_keyword,n_agent",
    [
        ("CTL", "A (p until q)", None),
        ("LTL", "p until q", None),
        ("OL", "<J1>p until q", None),
    ],
)
def test_temporal_keyword_parsed_not_as_prop(logic, formula_with_keyword, n_agent):
    """Temporal keywords (until, next, etc.) must be parsed as operators, not PROP."""
    parser_module = {
        "CTL": ("model_checker.parsers.formulas.CTL.parser", "CTLParser"),
        "LTL": ("model_checker.parsers.formulas.LTL.parser", "LTLParser"),
        "OL": ("model_checker.parsers.formulas.OL.parser", "OLParser"),
    }
    mod_path, class_name = parser_module[logic]
    mod = importlib.import_module(mod_path)
    parser_class = getattr(mod, class_name)
    parser = parser_class()
    kwargs = {} if n_agent is None else {"n_agent": n_agent}
    result = parser.parse(formula_with_keyword, **kwargs)
    assert (
        result is not None
    ), f"{logic} should parse '{formula_with_keyword}' (until as UNTIL, not PROP)"
