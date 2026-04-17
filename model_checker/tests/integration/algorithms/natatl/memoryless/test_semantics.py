"""NatATL memoryless semantics: action-guarded strategies vs output."""

import pytest

from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import (
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


@pytest.mark.semantic
@pytest.mark.model_checking
class TestNatATLMemorylessSemantics:
    """Test NatATL memoryless strategy semantics."""

    def test_memoryless_strategy_suffices(self, temp_file):
        """Verify memoryless strategy is sufficient for simple reachability."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        file_path = temp_file(content)
        load_cgs_from_content(temp_file, content)

        result = model_checking("<{1}, 1>F p", file_path)

        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)
        assert result["Satisfiability"] is True

    def test_memoryless_strategy_maintains_globally(self, temp_file):
        """Verify memoryless strategy can maintain global property."""
        content = build_cgs_model_content(
            transitions=[["I", "a"], ["a", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["1"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        file_path = temp_file(content)

        result = model_checking("<{1}, 1>G p", file_path)

        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)
        assert result["Satisfiability"] is True
