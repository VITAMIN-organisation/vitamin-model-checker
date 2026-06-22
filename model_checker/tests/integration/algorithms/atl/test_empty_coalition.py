"""ATL model checking with empty coalition (CTL-A style semantics)."""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import model_checking


def _initial_state_satisfied(result) -> bool:
    init = str(result.get("initial_state", ""))
    if ": True" in init:
        return True
    if ": False" in init:
        return False
    raise AssertionError(f"Unexpected initial_state field: {init!r}")


@pytest.mark.semantic
@pytest.mark.model_checking
def test_empty_coalition_eventually_on_simple_atl_fixture(test_data_dir):
    model_file = test_data_dir / "CGS" / "ATL" / "atl_2agents_4states_simple.txt"
    result = model_checking("<> F (p || q)", str(model_file))
    assert "error" not in result
    assert _initial_state_satisfied(result) is True
