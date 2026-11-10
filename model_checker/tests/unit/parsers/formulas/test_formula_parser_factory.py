"""FormulaParserFactory keeps one parser per logic and thread."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
def test_concurrent_parses_do_not_share_errors_or_results():
    """Parsers hold state (errors), so threads must not see each other's parse."""
    cases = [
        ("Wallet_ATL", "<<1>>X p", True),
        ("Wallet_ATL", "<<3>>G r", False),
        ("ATL", "<1>F p", True),
        ("ATL", "<3>F p", False),
        ("CTL", "EF p", True),
        ("CTL", "F p", False),
    ]

    def parse_one(case):
        logic, formula, valid = case
        parser = FormulaParserFactory.get_parser_instance(logic)
        result = parser.parse(formula, n_agent=2)
        return formula, valid, result is not None, bool(parser.errors)

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(parse_one, cases * 30))

    for formula, valid, parsed, has_errors in outcomes:
        assert parsed is valid, formula
        assert has_errors is not valid, formula


@pytest.mark.unit
def test_unknown_logic_is_an_error_naming_it():
    """A typo in the logic name fails loudly instead of returning some other parser."""
    with pytest.raises(ImportError, match="NoSuchLogic"):
        FormulaParserFactory.get_parser_instance("NoSuchLogic")
