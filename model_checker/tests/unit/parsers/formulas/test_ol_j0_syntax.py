"""OL parser: reject zero-cost demonic prefix <J0>."""

import pytest

from model_checker.parsers.formulas.OL.parser import OLParser


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["<J0> F safe", "<J0>F safe"])
def test_ol_parser_rejects_j0_prefix(formula):
    parser = OLParser()
    assert parser.parse(formula, n_agent=1) is None
