"""OL integration tests: errors and cost-bounded semantics on fixtures."""

import pytest

from model_checker.algorithms.explicit.OL.OL import model_checking


def _initial_state_satisfied(result) -> bool:
    init = str(result.get("initial_state", ""))
    if ": True" in init:
        return True
    if ": False" in init:
        return False
    raise AssertionError(f"Unexpected initial_state field: {init!r}")


@pytest.mark.unit
@pytest.mark.model_checking
@pytest.mark.parametrize(
    "formula, expect_error",
    [
        ("INVALID_FORMULA", True),
        ("<J1> F nonexistent", True),
        ("<JF r", True),
        ("F r", True),
        ("<2> F r", True),
    ],
)
def test_ol_rejects_invalid_input(test_data_dir, formula, expect_error):
    model_file = (
        test_data_dir / "costCGS" / "OL" / "ol_2agents_medium_6states_costs.txt"
    )
    result = model_checking(formula, str(model_file))
    if expect_error:
        assert "error" in result or "Syntax error" in result.get("res", "")
    else:
        assert "error" not in result


@pytest.mark.semantic
@pytest.mark.model_checking
@pytest.mark.parametrize(
    "formula, expected",
    [
        ("<J1> F r", False),
        ("<J2> F r", True),
    ],
)
def test_ol_medium_fixture_reachability(test_data_dir, formula, expected):
    """Min accumulated cost from s0 to r is 2 on the medium fixture."""
    model_file = (
        test_data_dir / "costCGS" / "OL" / "ol_2agents_medium_6states_costs.txt"
    )
    result = model_checking(formula, str(model_file))
    assert _initial_state_satisfied(result) is expected


@pytest.mark.semantic
@pytest.mark.model_checking
@pytest.mark.parametrize(
    "formula, expected",
    [
        ("<J26> F goal", False),
        ("<J27> F goal", True),
        ("<J1> G safe", True),
        ("<J2> G safe", False),
        ("<J1> X safe", True),
        ("<J1> X !goal", True),
        ("<J30> safe U goal", False),
        ("<J30> !goal U goal", True),
        ("<J30> safe R goal", False),
        ("<J30> !goal W goal", False),
        ("<J0> F (safe && goal)", False),
    ],
)
def test_ol_testvitamin_cost_bounded_operators(test_data_dir, formula, expected):
    """Regression suite for cost-bounded OL operators on the testvitamin fixture."""
    model_file = test_data_dir / "costCGS" / "OL" / "ol_testvitamin_2agents_8states.txt"
    result = model_checking(formula, str(model_file))
    assert "error" not in result
    assert _initial_state_satisfied(result) is expected
