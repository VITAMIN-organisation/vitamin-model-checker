"""NatATL Recall: scenarios where memory (recall) is required, vs memoryless ATL."""

import pytest

from model_checker.algorithms.explicit.NatATL.Recall.natatl_recall import (
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


@pytest.mark.integration
@pytest.mark.semantic
class TestNatATLRecallCritical:
    """Test scenarios where Perfect Recall is essential."""

    def test_recall_needed_for_ambiguous_path(self, temp_file):
        """Verify scenarios where agent must remember past state to choose action."""
        content = build_cgs_model_content(
            transitions=[
                ["I", "a", "0", "0"],  # s0->s0(I), s0->s1(a)
                ["0", "I", "a", "0"],  # s1->s1(I), s1->s2(a)
                ["0", "0", "I", "a"],  # s2->s2(I), s2->s3(a)
                ["0", "0", "0", "I"],  # s3->s3(I)
            ],
            state_names=["s0", "s1", "s2", "s3"],
            initial_state="s0",
            # s0, s1, s2 have 'processing' (1), 'goal' (0)
            # s3 has 'processing' (0), 'goal' (1)
            labelling=[["1", "0"], ["1", "0"], ["1", "0"], ["0", "1"]],
            num_agents=1,
            prop_names=["processing", "goal"],
        )
        parser = load_cgs_from_content(temp_file, content)

        formula = "<{1}, 1> F goal"
        result = model_checking(formula, parser.filename)

        assert (
            "error" not in result
        ), f"Model checking returned error: {result.get('error')}"
        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)
        assert result.get("Complexity Bound") <= 4

    def test_recall_unsatisfiable_formula_returns_false(self, temp_file):
        """When goal is only at a state that is unreachable from s0, Satisfiability is False."""
        content = build_cgs_model_content(
            transitions=[
                ["0", "I", "0"],
                ["0", "I", "0"],
                ["0", "0", "I"],
            ],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0"], ["0"], ["1"]],
            num_agents=1,
            prop_names=["goal"],
        )
        cgs = load_cgs_from_content(temp_file, content)
        result = model_checking("<{1}, 1>F goal", cgs.filename)
        assert "error" not in result
        assert "Satisfiability" in result
        assert result["Satisfiability"] is False
