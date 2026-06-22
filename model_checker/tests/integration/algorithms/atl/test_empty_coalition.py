"""ATL model checking rejects empty coalition <>."""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import model_checking


@pytest.mark.semantic
@pytest.mark.model_checking
def test_empty_coalition_eventually_rejected_on_simple_atl_fixture(test_data_dir):
    model_file = test_data_dir / "CGS" / "ATL" / "atl_2agents_4states_simple.txt"
    result = model_checking("<> F (p || q)", str(model_file))
    assert "error" in result or "Syntax error" in result.get("res", "")
