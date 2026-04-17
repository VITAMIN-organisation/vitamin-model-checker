"""OL model checking: cost bounds, error cases and basic semantics."""

import pytest

from model_checker.algorithms.explicit.OL.OL import (
    _core_ol_checking,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    load_test_model,
)


@pytest.mark.unit
@pytest.mark.model_checking
class TestOLErrorHandling:
    """Test OL error handling for invalid inputs."""

    def test_ol_invalid_formula_syntax(self, test_data_dir):
        """Test OL with invalid formula syntax."""
        model_file = (
            test_data_dir / "costCGS" / "OL" / "ol_2agents_medium_6states_costs.txt"
        )

        result = model_checking("INVALID_FORMULA", str(model_file))
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_ol_nonexistent_atomic_proposition(self, test_data_dir):
        """Test OL with non-existent atomic proposition."""
        parser = load_test_model(
            test_data_dir,
            "costCGS/OL/ol_2agents_medium_6states_costs.txt",
        )

        # Use atomic proposition that doesn't exist
        result = _core_ol_checking(parser, "<1><5>F nonexistent")
        assert "error" in result or "does not exist" in result.get("res", "").lower()

    def test_ol_invalid_coalition(self, test_data_dir):
        """Test OL with invalid coalition (agent number out of range)."""
        parser = load_test_model(
            test_data_dir,
            "costCGS/OL/ol_2agents_medium_6states_costs.txt",
        )

        result = _core_ol_checking(parser, "<99><5>F p")
        assert "error" in result

    def test_ol_missing_cost_bound(self, test_data_dir):
        """Test OL with missing cost bound (should require cost bound)."""
        parser = load_test_model(
            test_data_dir,
            "costCGS/OL/ol_2agents_medium_6states_costs.txt",
        )

        # OL requires cost bound syntax: <A><n>
        # Missing cost bound should be invalid
        result = _core_ol_checking(parser, "<1>F p")
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_ol_negative_cost_bound(self, test_data_dir):
        """Test OL with negative cost bound (should be invalid)."""
        parser = load_test_model(
            test_data_dir,
            "costCGS/OL/ol_2agents_medium_6states_costs.txt",
        )

        result = _core_ol_checking(parser, "<1><-5>F p")
        assert "error" in result


@pytest.mark.semantic
@pytest.mark.model_checking
class TestOLSemantics:
    """Semantic OL tests using the standard OL fixture model."""

    def test_ol_eventually_with_sufficient_cost_bound(self, test_data_dir):
        """<J1>F r should hold in all states of the standard OL fixture (regression for known semantics)."""
        model_file = (
            test_data_dir / "costCGS" / "OL" / "ol_2agents_medium_6states_costs.txt"
        )

        result = model_checking("<J1>F r", str(model_file))
        states = extract_states_from_result(result)

        assert states == {"s0", "s1", "s2", "s3", "s4", "s5"}

    def test_ol_eventually_other_atom(self, test_data_dir):
        """<J1>F a on the same fixture returns a non-empty state set (a holds at s3, s5)."""
        parser = load_test_model(
            test_data_dir,
            "costCGS/OL/ol_2agents_medium_6states_costs.txt",
        )
        result = _core_ol_checking(parser, "<J1>F a")
        assert "error" not in result
        assert "res" in result
        states = extract_states_from_result(result)
        assert states is not None
        assert len(states) >= 1
        assert states <= {"s0", "s1", "s2", "s3", "s4", "s5"}
        assert "s5" in states
